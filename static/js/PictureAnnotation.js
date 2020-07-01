var new_url = ''; //用于记录当前编辑的图片在服务器中的位置
var user_ip = '0.0.0.0';//用于记录当前访问者的Ip
var user_address = '无';//用于记录当前ip位置
var timer = null; //监听器

const mappingStyles = {
    drawRect: {
        drawStyle: {strokeColor: '#FF0000', opacity: 1, lineWeight: 1},
        featureStyle: {strokeColor: '#FF0000', fillColor: '#0000FF', opacity: .3, lineWeight: 1}
    },
    drawPolygon: {
        drawStyle: {strokeColor: '#00FF00', opacity: 1, lineWeight: 1},
        featureStyle: {strokeColor: '#FF0000', fillColor: '#00FF00', opacity: .3, lineWeight: 1}
    },
    drawMask: {
        drawStyle: {strokeColor: '#FF0000', fillColor: '#0000FF', opacity: 1, lineWeight: 1},
        featureStyle: {}
    },
    clearMask: {
        drawStyle: {lineWeight: 20},
        featureStyle: {}
    },
    drawPoint: {
        drawStyle: {pointRadius: 5},
        featureStyle: {strokeColor: '#0000FF', fillColor: '#8B008B', opacity: 1, pointRadius: 5}
    },
    drawPolyline: {
        drawStyle: {strokeColor: '#FF0000', fillColor: '#0000FF', opacity: 1, lineWeight: 10},
        featureStyle: {strokeColor: '#0000FF', fillColor: '#FF0000', opacity: 1, lineWeight: 10}
    },
    pan: {
        drawStyle: {},
        featureStyle: {}
    }
};

const timestamp = new Date().getTime();

function setMode(mode, color, size) {
    const preCurrentMode = mode.indexOf('drawMask') === 0 ? 'drawMask' : mode;
    const currentMode = preCurrentMode.indexOf('drawPolyline') === 0 ? 'drawPolyline' : preCurrentMode;
    const drawStyle = mappingStyles[currentMode].drawStyle;
    if (color) {
        if (currentMode === 'drawPolyline') {
            drawStyle.strokeColor = color;
        }
        else {
            drawStyle.fillColor = color;
        }
    }
    if (size) {
        drawStyle.lineWeight = size;
    }

    gMap && gMap.setMode(currentMode, new AILabel.Style(drawStyle));

    document.getElementById('drawRect').style.backgroundColor = '#fff';
    document.getElementById('drawPolygon').style.backgroundColor = '#fff';
    document.getElementById('pan').style.backgroundColor = '#fff';

    document.getElementById(mode).style.backgroundColor = '#3377ff';
}




function isConfirm($this) {
    //（当前图片标注将会全部消失，请在确认保存后执行此操作）
    if(confirm("确认要更换图片吗？")){
        setPicUrl($($this));
    }else{
        $($this).val('');
    }
}

//获取当前访问者的ip地址和位置
function getIp() {
    $.getScript('http://pv.sohu.com/cityjson?ie=utf-8',
        function(){
            user_ip = returnCitySN ['cip'];
            user_address = returnCitySN ['cname'];
            getPictures();
        })
}


// 该事件用来监听文件上传控件是否选择好指定文件
function setPicUrl($this) {
    //获取文件选择控件选择的图片对象
    //let file_c = document.getElementById('file');
    let file_c = $($this).get(0);
    // files是input[type=file]的属性， 用来存储文件选择控件选择的图片对象， 是一个数组类型
    let file_obj = file_c.files[0];
    // 将文件类型的数据打包成form表单数据
    let formD = new FormData();
    formD.append('file',file_obj);
    formD.append('ip',user_ip);
    formD.append('address',user_address);
    //alert(file_obj);
    $.ajax({
        // 先上传图片到服务器
        url:'file_upload/',
        type:'post',
        data:formD,
        // 数据传输过程中不需要将数据转换成字符串
        processData:false,
        // ajax传输数据过程中不需要重新设置数据的编码格式
        contentType:false,
        success:function (res) {
            let msg = JSON.parse(res);
            let code = msg.code;
            if(code == 200){
                new_url = msg.url;
                let width = msg.width;
                let height = msg.height;
                let ip = msg.ip;
                let address = msg.address;
                let timeStr = msg.time;
                if (typeof(map_width) == 'undefined') {
                   map_width = $('#map').width();
                }
                //console.log(width);
                //console.log(height);
                //如果图片宽度大于div宽度，则等比例缩小
                /**
                if(width > map_width){
                   height = height * (map_width/width);
                   width = map_width;
                }
                **/
                //重置div的高度
                $('#map').height(height);
                $('#map').width(width);
                // 工具栏宽度
                /**
                if(width < 0.43 * map_width)
                    $('#tool').width(0.43 * map_width);
                else
                    $('#tool').width(width);
                **/

                //如果存在gImageLayer（其他图片）则先删除掉
                if(gImageLayer != null)
                    gMap.removeLayer(gImageLayer);
                //然后再新建一个Layer展示新的图片
                gImageLayer = new AILabel.Layer.Image('img', new_url, {w: width, h: height}, {
                    zIndex: 1,
                    //grid: {rowCount: 3, columnCount: 3}
                });
                //重置gMap画布大小
                gMap.resize(width,height);
                //重置gMap中心点
                //gMap.setCenter(0,0);
                gMap.addLayer(gImageLayer);
                //移除文字
                gMap.removeLayer(gTextLayer);
                //移除矢量要素
                gFeatureLayer.removeAllFeatures();
                //删除所有其他标注点
                gMap.mLayer.removeAllMarkers();

                //刷新已编辑图片下拉框
                getPictures();
                //清空标注内容下拉框 并添加上“请选择”的选项
                $('#annotation_select').empty();
                $('#annotation_select').prepend("<option value='0' selected>--请选择--</option>");
                //显示图片信息
                $('#picInfos').show();
                $('#anno_user_ip').text(ip);
                $('#anno_user_address').text(address);
                $('#anno_time').text(timeStr);
                $('#delPictureBtn').show();
            }else{
                alert("抱歉，该图片上传时出错，请重新上传");
            }

        }
    });
}

//获取多边形质心
function get_polygon_centroid(pts) {
   var first = pts[0], last = pts[pts.length-1];
   if (first.x != last.x || first.y != last.y) pts.push(first);
   var twicearea=0,
   x=0, y=0,
   nPts = pts.length,
   p1, p2, f;
   for ( var i=0, j=nPts-1 ; i<nPts ; j=i++ ) {
      p1 = pts[i]; p2 = pts[j];
      f = p1.x*p2.y - p2.x*p1.y;
      twicearea += f;
      x += ( p1.x + p2.x ) * f;
      y += ( p1.y + p2.y ) * f;
   }
   f = twicearea * 3;
   return { x:x/f, y:y/f };
}


//绘制完成时执行的操作
function afterGeometryDrawDone() {
    gMap.events.on('geometryDrawDone', function (type, points, options) {
        const cMode = gMap.getMode();
        //console.log('--points--', points, options);
        //绘制完后提示输入标注信息
        window.wxc.xcConfirm("请输入标注信息：", window.wxc.xcConfirm.typeEnum.input,{
            onOk:function(v){
                if(v == ''){
                    alert("输入内容不能为空，请重新标注");
                    return 0;
                }
                //console.log(v);
                let polygon_centroid = get_polygon_centroid(points);
                //console.log(polygon_centroid);
                //console.log(polygon_centroid.x);
                //console.log(polygon_centroid.y);
                //删除所有其他标注点
                gMap.mLayer.removeAllMarkers();
                 //marker对象实例\添加
                const marker = new AILabel.Marker('markerImg', {
                    src: '../static/images/marker.png',
                    x: polygon_centroid.x,
                    y: polygon_centroid.y,
                    offset: {x: -32, y: -32},
                });
                gMap.mLayer.addMarker(marker);
                //删除所有其他标注区域
                gFeatureLayer.removeAllFeatures();
                const featureStyle = mappingStyles[cMode].featureStyle;
                // 元素添加展示
                // 生成元素唯一标志（时间戳）
                if (type === 'point') {
                    const {radius = 5} = options || {};
                    let fea = new AILabel.Feature.Point(`feature-${timestamp}`, points, {
                        name: 'name_point'
                    }, featureStyle);
                    gFeatureLayer.addFeature(fea);
                }
                if (type === 'rect') {
                    let fea = new AILabel.Feature.Rect(`feature-${timestamp}`, points, {
                        name: 'name_rect'
                    }, featureStyle);
                    gFeatureLayer.addFeature(fea);
                }
                else if (type === 'polygon') {
                    let fea = new AILabel.Feature.Polygon(`feature-${timestamp}`, points, {
                        name: 'name_polygon'
                    }, featureStyle);
                    gFeatureLayer.addFeature(fea);
                }
                else if (type === 'polyline') {
                    const {width = 5} = options || {};
                    let fea = new AILabel.Feature.Polyline(`feature-${timestamp}`, points, {
                        name: 'name_polyline'
                    }, featureStyle, {width});
                    gFeatureLayer.addFeature(fea);
                }
                else if (type === 'mask') {
                    gMaskLayer.addMasks(points);
                }

                //准备参数
                let postData = new FormData();
                postData.append('url',new_url);
                //console.log(new_url);
                postData.append('points',JSON.stringify(points));
                postData.append('ctext',v);
                postData.append('type',type);
                //console.log(points);
                //发Ajax请求给服务器处理图片（需传参图片地址、选择区域的数组、标注内容）
                let token = $.cookie('csrftoken');
                $.ajax({
                    url: 'cut_pic/',
                    type: 'POST',
                    data: postData,
                    async: true,//同步上传
                    cache: false,//缓存
                    processData: false,  // 不处理数据
                    contentType: false, // 不设置内容类型
                    headers: {
                        'X-CSRFToken': token
                    },
                    success:function (res) {
                        let msg = JSON.parse(res);
                        let code = msg.code;
                        if(code == 200){
                            //console.log(msg.url);
                            $('#annotation_img').attr('src',msg.url);
                            $('#annotation_text').text(v);
                            $('#annotation_time').text(msg.time);
                            $('#annotation_select').prepend("<option value='"+msg.annotation_id+"' selected>"+v+"</option>");
                            $("#annotation_select option[value='0']").remove();
                            $('#annotation').show();
                            $('#tips').show();
                            $('#deleteAnnotationBtn').show();
                            $('#updateAnnotationBeforeBtn').show();
                        }else{
                            alert(msg.msg);
                        }
                    }
                });
            }
        });
    });
}

//修改标注的函数（可复用）
function changeAnnotationInfoFun(msg) {
    //console.log(msg);
    let annotation_id = msg.annotation_id;
    //console.log(new_url);
    //修改下半部分展示界面（标注展示区）
    $('#annotation_img').attr('src',msg.url);
    $('#annotation_text').text(msg.text);
    $('#annotation_time').text(msg.time);
    if(msg.fun_type == 'selectChange'){
        $("#annotation_select option[value='0']").remove();
        $('#annotation').show();
        $('#tips').show();
        $('#deleteAnnotationBtn').show();
        $('#updateAnnotationBeforeBtn').show();
    }else if(msg.fun_type == 'delAnnotation'){
        if(msg.url == 'null'){
            $("#annotation_select").empty();
            $('#annotation_select').prepend("<option value='0' selected>--请选择--</option>");
            $('#annotation_img').attr('src','../static/images/bg.png');
            $('#annotation').hide();
            $('#tips').hide();
            $('#deleteAnnotationBtn').hide();
            $('#updateAnnotationBeforeBtn').hide();
            //删除所有其他标注点
            gMap.mLayer.removeAllMarkers();
            //删除所有其他标注区域
            gFeatureLayer.removeAllFeatures();
            return 0;
        }else{
            $("#annotation_select").find("option").get($("#annotation_select").get(0).selectedIndex).remove();
            $("#annotation_select").val(msg.annotation_min);
            $('#annotation_img').attr('src',msg.url);
        }
    }

    //修改上半部分展示界面（原图）
    //console.log(msg);
    const cMode = gMap.getMode();
    let polygon_centroid = get_polygon_centroid(JSON.parse(msg.points));
    //删除所有其他标注点
    gMap.mLayer.removeAllMarkers();
    //marker对象实例\添加
    const marker = new AILabel.Marker('markerImg', {
        src: '../static/images/marker.png',
        x: polygon_centroid.x,
        y: polygon_centroid.y,
        offset: {x: -32, y: -32},
    });
    gMap.mLayer.addMarker(marker);
    //删除所有其他标注区域
    gFeatureLayer.removeAllFeatures();
    const featureStyle = mappingStyles[cMode].featureStyle;
    // 元素添加展示
    // 生成元素唯一标志（时间戳）
    if (msg.type === 'rect') {
        let fea = new AILabel.Feature.Rect(`feature-${timestamp}`, JSON.parse(msg.points), {
            name: 'name_rect'
        }, featureStyle);
        gFeatureLayer.addFeature(fea);
    }
    else if (msg.type === 'polygon') {
        let fea = new AILabel.Feature.Polygon(`feature-${timestamp}`, JSON.parse(msg.points), {
            name: 'name_polygon'
        }, featureStyle);
        gFeatureLayer.addFeature(fea);
    }
}

//监听select，改变时发Ajax请求获取要查看的图片的AnnotationInfo
function changeAnnotationInfo() {
    let annotation_id = $('#annotation_select option:selected').val();
    if(new_url == ""){//当前编辑的图片的url
        alert("未检测到当前图片，请刷新页面重试");
        return 0;
    }
    //准备参数
    let postData = new FormData();
    postData.append('annotation_id',annotation_id);
    postData.append('old_url',new_url);
    //发Ajax请求给服务器获取ROI相关信息（图片地址、标注内容、标注时间）
    $.ajax({
        url:'get_url/',
        type:'POST',
        data:postData,
        async: true,//同步上传
        cache: false,//上传文件无需缓存
        processData: false,  // 不处理数据
        contentType: false, // 不设置内容类型
        success:function (res) {
            let msg = JSON.parse(res);
            let code = msg.code;
            if(code == 200){
                msg.fun_type = 'selectChange';
                changeAnnotationInfoFun(msg);
            }else{
                alert(msg.msg);
            }
        }
    });
}

//获取pic_select的option
function getPictures() {
    //if($('#pic_select option:selected').val() != '0')
        //return 0;
    //发Ajax请求给服务器获取所有已经标注过的图片
    let postData = new FormData();
    //alert(user_ip);
    postData.append('ip',user_ip);
    let token = $.cookie('csrftoken');
    $.ajax({
        url: 'get_pics/',
        type: 'POST',
        data: postData,
        async: true,//同步上传
        cache: false,//缓存
        processData: false,  // 不处理数据
        contentType: false, // 不设置内容类型
        headers: {
            'X-CSRFToken': token
        },
        success: function (res) {
            let msg = JSON.parse(res);
            let code = msg.code;
            if (code == 200) {
                //将图片List加载到select中
                //console.log(msg.picList);
                let picListJson = JSON.parse(msg.picList);
                //console.log(picListJson);
                $('#pic_select').empty();
                for(let key in picListJson){
                    //console.log(key);
                    $('#pic_select').prepend("<option value='"+picListJson[key]['url']+"'>"+key+"</option>");
                }
                $('#pic_select').prepend("<option value='0' selected>--请选择--</option>");
            }else{
                alert(msg.msg);
            }
        }
    });
}

//监听pic_select发生变化时，执行Ajax加载老图片
function selectOldPic() {
    $("#pic_select option[value='0']").remove();
    let src = $('#pic_select option:selected').val();
    //发Ajax请求给服务器获取已选择的旧图片的所有信息及其所有标注信息
    let postData = new FormData();
    postData.append('pic_url',src);
    let token = $.cookie('csrftoken');
    $.ajax({
        url: 'get_pic_infos/',
        type: 'POST',
        data: postData,
        async: true,//同步上传
        cache: false,//缓存
        processData: false,  // 不处理数据
        contentType: false, // 不设置内容类型
        headers: {
            'X-CSRFToken': token
        },
        success: function (res) {
            let msg = JSON.parse(res);
            let code = msg.code;
            if (code == 200) {
                //console.log(JSON.parse(msg.picList));
                let picInfo = JSON.parse(msg.picList);
                new_url = 'static/' + picInfo.url;
                let width = picInfo.width;
                let height = picInfo.height;
                if (typeof(map_width) == 'undefined') {
                   map_width = $('#map').width();
                }
                //重置div的高度
                $('#map').height(height);
                $('#map').width(width);
                //如果存在gImageLayer（其他图片）则先删除掉
                if(gImageLayer != null)
                    gMap.removeLayer(gImageLayer);
                //然后再新建一个Layer展示新的图片
                gImageLayer = new AILabel.Layer.Image('img', new_url, {w: width, h: height}, {
                    zIndex: 1,
                });
                //重置gMap画布大小
                gMap.resize(width,height);
                //重置gMap中心点
                //gMap.setCenter(0,0);
                gMap.addLayer(gImageLayer);
                //移除文字
                gMap.removeLayer(gTextLayer);
                //移除矢量要素
                gFeatureLayer.removeAllFeatures();
                //删除所有其他标注点
                gMap.mLayer.removeAllMarkers();

                //让选择文件框的内容变为空
                $('#pic').val('');
                $('#delPictureBtn').show();
                //显示图片信息
                $('#picInfos').show();
                $('#anno_user_ip').text(picInfo.ip);
                $('#anno_user_address').text(picInfo.address);
                $('#anno_time').text(picInfo.time);

                //console.log($.isEmptyObject(picInfo.annoList));

                //将已标注信息加载到anno_select中
                $('#annotation_select').empty();
                $('#annotation').hide();
                $('#annotation_select').append("<option value='0'>--请选择--</option>");
                if(!$.isEmptyObject(picInfo.annoList)){
                    for(let i in picInfo.annoList){
                        if(i==0){
                            $('#annotation_select').append("<option value='"+picInfo.annoList[i].annotation_id+"' selected>"
                                +picInfo.annoList[i].annotation_text+"</option>");
                        }else{
                            $('#annotation_select').append("<option value='"+picInfo.annoList[i].annotation_id+"'>"
                                +picInfo.annoList[i].annotation_text+"</option>");
                        }
                    }
                }
            }else{
                alert(msg.msg);
            }
        }
    });
}

//删除某个标注
function deleteAnnotation(){
    let annotation_id = $('#annotation_select option:selected').val();
    //Ajax请求删除图片以及数据库中的标注信息
    let postData = new FormData();
    postData.append('pic_url',new_url);
    postData.append('annotation_id',annotation_id);
    let token = $.cookie('csrftoken');
    $.ajax({
        url: 'del_annotation/',
        type: 'POST',
        data: postData,
        async: true,//同步上传
        cache: false,//缓存
        processData: false,  // 不处理数据
        contentType: false, // 不设置内容类型
        headers: {
            'X-CSRFToken': token
        },
        success: function (res) {
            let msg = JSON.parse(res);
            if(msg.code == 200){
                msg.fun_type = 'delAnnotation';
                msg.annotation_id = annotation_id;
                changeAnnotationInfoFun(msg);
            }else{
                alert(msg.msg);
            }
        }
    });
}

//删除某张图片及其所有标注
function delPicture() {
    //（当前图片标注将会全部消失，请在确认保存后执行此操作）
    if(confirm("确认要删除当前图片吗？（删除后所有标注也将被删除，且此操作不可逆）")){
        //Ajax请求删除图片以及所有的标注信息
        let postData = new FormData();
        postData.append('pic_url',new_url);
        let token = $.cookie('csrftoken');
        $.ajax({
            url: 'del_picture/',
            type: 'POST',
            data: postData,
            async: true,//同步上传
            cache: false,//缓存
            processData: false,  // 不处理数据
            contentType: false, // 不设置内容类型
            headers: {
                'X-CSRFToken': token
            },
            success: function (res) {
                let msg = JSON.parse(res);
                if(msg.code == 200){
                    //重置map
                    $('#map').height('500px');
                    $('#map').width('80%');
                    //如果存在gImageLayer（其他图片）则先删除掉
                    if(gImageLayer != null)
                        gMap.removeLayer(gImageLayer);
                    //重置gMap画布大小
                    gMap.resize($('#map').width(),$('#map').height());
                    //移除矢量要素
                    gFeatureLayer.removeAllFeatures();
                    //删除所有其他标注点
                    gMap.mLayer.removeAllMarkers();
                    const gTextStyle = new AILabel.Style({fontColor: '#696969', fontSize: 20, strokeColor: '#0000FF', opacity: 0});
                    // 文本层实例\添加
                    let gTextLayer = new AILabel.Layer.Text('textLayer', {zIndex: 2});
                    gMap.addLayer(gTextLayer);
                    // 文本实例\添加
                    const text = new AILabel.Text('id', {
                        pos: {x: -50, y: 60},
                        offset: {x: -180, y: 0},
                        width: 600,
                        maxWidth: 400,
                        text: '请点击下方选择文件按钮选择一张要编辑的图片'
                    }, gTextStyle);
                    const text2 = new AILabel.Text('id', {
                        pos: {x: -50, y: 30},
                        offset: {x: -210, y: 0},
                        width: 600,
                        maxWidth: 400,
                        text: '或在“选择已编辑的图片”下拉框中选择已编辑的图片'
                    }, gTextStyle);
                    gTextLayer.addText(text);
                    gTextLayer.addText(text2);

                    //隐藏图片的信息
                    $('#picInfos').hide();

                    //将pic_select的val变为0（“请选择的状态”）并删除当前选中项
                    if($('#pic_select option:selected').val() != '0'){
                        $("#pic_select").find("option").get($("#pic_select").get(0).selectedIndex).remove();
                        $('#pic_select').prepend("<option value='0' selected>--请选择--</option>")
                    }

                    //让选择文件框的内容变为空
                    $('#pic').val('');

                    //隐藏删除图片的按钮
                    $('#delPictureBtn').hide();

                    //隐藏标注信息区域
                    $('#annotation').hide();
                    $('#tips').hide();

                    //清空annotation_select 并添加请选择
                    $('#annotation_select').empty();
                    $('#annotation_select').prepend("<option value='0' selected>--请选择--</option>");

                    //隐藏编辑标注和删除标注的button
                    $('#updateAnnotationBeforeBtn').hide();
                    $('#deleteAnnotationBtn').hide();
                }else{
                    alert(msg.msg);
                }
            }
        });
    }
}

//更新标注区域的前置函数
function updateAnnotationBefore() {
    //console.log(gFeatureLayer.getAllFeatures()[0]);
    //让选区变为active状态
    gFeatureLayer.getAllFeatures()[0].active();
    //删除Marker
    gMap.mLayer.removeAllMarkers();
    //隐藏前置button
    $("#updateAnnotationBeforeBtn").hide();
    //显示后置button
    $("#updateAnnotationAfterBtn").show();
    //监听active是否发生变化了
    timer=setInterval(function() {
            //console.log();
            if(!gFeatureLayer.getAllFeatures()[0]['activeStatus']){
                clearInterval(timer);
                updateAnnotationAfter();
            }
        },1000);
}

//更新标注区域的后置函数
function updateAnnotationAfter() {
    //console.log((gFeatureLayer.getAllFeatures()[0]['points']));
    let points = gFeatureLayer.getAllFeatures()[0]['points'];
    let pointsStr = JSON.stringify(points);
    //让标注区域禁止编辑
    gFeatureLayer.getAllFeatures()[0].deActive();
    //重新绘制maker
    let polygon_centroid = get_polygon_centroid(points);
    const marker = new AILabel.Marker('markerImg', {
        src: '../static/images/marker.png',
        x: polygon_centroid.x,
        y: polygon_centroid.y,
        offset: {x: -32, y: -32},
    });
    gMap.mLayer.addMarker(marker);

    //发Ajax请求，修改图片
    //Ajax请求删除图片以及所有的标注信息
    let postData = new FormData();
    postData.append('url',new_url);
    postData.append('annotation_id',$('#annotation_select option:selected').val());
    postData.append('points',pointsStr);
    let token = $.cookie('csrftoken');
    $.ajax({
        url: 'update_annotation_pic/',
        type: 'POST',
        data: postData,
        async: true,//同步上传
        cache: false,//缓存
        processData: false,  // 不处理数据
        contentType: false, // 不设置内容类型
        headers: {
            'X-CSRFToken': token
        },
        success: function (res) {
            let msg = JSON.parse(res);
            if(msg.code == 200){
                $('#annotation_img').attr('src',msg.url + '?' + new Date().getTime());
                $('#annotation_time').text(msg.time);
            }else{
                alert(msg.msg);
            }
        }
    });

    //隐藏后置button
    $("#updateAnnotationAfterBtn").hide();
    //显示前置button
    $("#updateAnnotationBeforeBtn").show();
}

//修改标注的内容前置
function changeAnnotationTextBefore(){
    //两按钮交替显示
    $('#changeTextBeforeBtn').hide();
    $('#changeTextAfterBtn').show();
    $('#annotation_text').hide();
    $('#text_input').val($('#annotation_text').text());
    $('#text_input').show();

}

//修改标注的内容后置
function changeAnnotationTextAfter(){
    let new_text = $('#text_input').val();
    //Ajax请求修改标注信息的内容
    let postData = new FormData();
    postData.append('pic_url',new_url);
    postData.append('annotation_id',$('#annotation_select option:selected').val());
    postData.append('new_text',new_text);
    let token = $.cookie('csrftoken');
    $.ajax({
        url: 'update_annotation_text/',
        type: 'POST',
        data: postData,
        async: true,//同步上传
        cache: false,//缓存
        processData: false,  // 不处理数据
        contentType: false, // 不设置内容类型
        headers: {
            'X-CSRFToken': token
        },
        success: function (res) {
            let msg = JSON.parse(res);
            if(msg.code == 200){
                $('#annotation_text').text(msg.text);
                $('#annotation_time').text(msg.time);
                $('#annotation_select option:selected').text(msg.text)
            }else{
                alert(msg.msg);
            }
        }
    });


    //两按钮交替显示
    $('#changeTextAfterBtn').hide();
    $('#changeTextBeforeBtn').show();
    $('#text_input').hide();
    $('#annotation_text').show();
}




