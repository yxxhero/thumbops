layui.use(["element","table","layer"],
function() {
    var $ = layui.jquery,
    layer = layui.layer,table = layui.table;
    var notyf = new Notyf();
    var tableIns = table.render({
        elem: '#tasktable'
        ,url: '/tasklist'
        ,id: 'taskins'
        ,initSort: {
        field: 'date'
        ,type: 'desc'
         }
        ,cellMinWidth:100 
        ,page:true
        ,cols: [[ 
          {field: 'date', title: '日期',sort:true}
          ,{field: 'taskid', title: '任务id'}
          ,{field: 'title', title: '标题'}
          ,{field: 'total', title: '合计'}
          ,{field: 'percent', title: '百分比'} 
          ,{field: 'status', title: '状态', align:'center'} 
          ,{fixed: 'right', align:'center', toolbar: '#barDemo'}
        ]]
      });
    var addbt = document.getElementById("addbutton");
    addbt.onclick = function tst(){ 
       var processesnum = $("#processesnum").val();
       var wbmid = $("#wbmid").val();
       var upnum = $("#upnum").val();
       var index = layer.load();
       $.ajax({
    url:'/handle',
    type:'POST',
    async:true, 
    data:{
        "processesnum":processesnum,"wbmid":wbmid,"upnum":upnum
    },
    timeout:5000,
    dataType:'json',
    success:function(data){
        if(data.error == 1){
        layer.close(index);
        layer.msg(data.msg, {icon: 2}); 
       }else{
        layer.close(index);
        layer.msg(data.msg, {icon: 1}); 
        tableIns.reload();
        }
    }
}); 
    }
function checkproc(){
       $.ajax({
    url:'/api/checkproc',
    type:'GET',
    async:true, 
    timeout:5000,
    dataType:'json',
    success:function(data){
        if(data.error == 1){
         notyf.alert('任务处理进程不存在，请查看原因并启动....');
       }else{
         notyf.confirm('任务处理检测正常...');
        }
    }
}); 

}
function updatetable(){
tableIns.reload();
} 

var checkth=setInterval(checkproc,30000);
var uptable=setInterval(updatetable,5000);
table.on('tool(tasklt)', function(obj){ 
  var data = obj.data; 
  var layEvent = obj.event;
  var tr = obj.tr;
 
  if(layEvent === 'detail'){ 
   console.log(data);
       $.ajax({
    url:'/taskhandle',
    type:'POST',
    async:true, 
    data:{
        "method":"start","id":data.id
    },
    timeout:3000,
    dataType:'json',
    success:function(data){
        if(data.error == 1){
        layer.msg(data.msg, {icon: 2}); 
       }else{
        layer.msg(data.msg, {icon: 1}); 
        tableIns.reload();
        }
    }
}); 
  } else{
    layer.confirm('真的删除行么', function(index){
       $.ajax({
    url:'/taskhandle',
    type:'POST',
    async:true, 
    data:{
        "method":"del","id":data.id
    },
    timeout:5000,
    dataType:'json',
    success:function(data){
        if(data.error == 1){
        layer.close(index);
        layer.msg(data.msg, {icon: 2}); 
       }else{
        layer.close(index);
        layer.msg(data.msg, {icon: 1}); 
        tableIns.reload();
        }
    }
}); 
      
      obj.del();
      layer.close(index);
    });
  }
});
     
});
