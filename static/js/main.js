// 主函数

window.console = console ? console : {"dir":function(){},"info":function(){}}


function selectAll(ele,oId) {
	var _checked = $(ele).is(':checked'),
		checkboxs = $("#" + oId + " input[type='checkbox']:visible");
	checkboxs.each(function(i,ele) {
		$(ele).prop('checked', _checked);
	});
}

function getArgs(){
    var args = {};
    var match = null;
    var search = decodeURIComponent(location.search.substring(1));
    var reg = /(?:([^&]+)=([^&]+))/g;
    while((match = reg.exec(search))!==null){
        args[match[1]] = match[2];
    }
    return args;
}

function valueReplace(v) {
	v = v.toString().replace(new RegExp('(["\"])', 'g'), "\\\"");
	return v;
}



// 时间类函数

//var s = "2006-12-13 09:41:30";
//var s2 = '2006-12-15 09:42:00';
function DateDiff(s, s2) {//sDate1和sDate2是2002-12-18格式
	var aDate, oDate1, oDate2, iDays;
	oDate1 = new Date(Date.parse(s.replace(/-/g, "/")));
	oDate2 = new Date(Date.parse(s2.replace(/-/g, "/")));

	iDays = parseInt(Math.abs(oDate1 - oDate2) / 1000 / 86399);
	if ((oDate1 - oDate2) < 0) {
		return -iDays;
	}
	return iDays;
}

/* 得到日期年月日等加数字后的日期 */ 
// interval 
// 设置	描述
// y	年
// q	季度
// m	月
// d	日
// w	周
// h	小时
// n	分钟
// s	秒
// ms	毫秒

Date.prototype.dateAdd = function(interval,number) 
{ 
    var d = this; 
    var k={'y':'FullYear', 'q':'Month', 'm':'Month', 'w':'Date', 'd':'Date', 'h':'Hours', 'n':'Minutes', 's':'Seconds', 'ms':'MilliSeconds'}; 
    var n={'q':3, 'w':7}; 
    eval('d.set'+k[interval]+'(d.get'+k[interval]+'()+'+((n[interval]||1)*number)+')'); 
    return d; 
} 
/* 计算两日期相差的日期年月日等 */ 
Date.prototype.dateDiff = function(interval,objDate2) 
{ 

    var d=this, i={}, t=d.getTime(), t2=objDate2.getTime(); 
    i['y']=objDate2.getFullYear()-d.getFullYear(); 
    i['q']=i['y']*4+Math.floor(objDate2.getMonth()/4)-Math.floor(d.getMonth()/4); 
    i['m']=i['y']*12+objDate2.getMonth()-d.getMonth(); 
    i['ms']=objDate2.getTime()-d.getTime(); 
    i['w']=Math.floor((t2+345600000)/(604800000))-Math.floor((t+345600000)/(604800000)); 
    i['d']=Math.floor(t2/86400000)-Math.floor(t/86400000); 
    i['h']=Math.floor(t2/3600000)-Math.floor(t/3600000); 
    i['n']=Math.floor(t2/60000)-Math.floor(t/60000); 
    i['s']=Math.floor(t2/1000)-Math.floor(t/1000); 
    return i[interval]; 
}

// 对Date的扩展，将 Date 转化为指定格式的String
// 月(M)、日(d)、小时(h)、分(m)、秒(s)、季度(q) 可以用 1-2 个占位符， 
// 年(y)可以用 1-4 个占位符，毫秒(S)只能用 1 个占位符(是 1-3 位的数字) 
// 例子： 
// (new Date()).Format("yyyy-MM-dd hh:mm:ss") ==> 2006-07-02 08:09:04.423 
// (new Date()).Format("yyyy-M-d h:m:s.S")      ==> 2006-7-2 8:9:4.18 
Date.prototype.Format = function (fmt) { //author: meizz 
    var o = {
        "M+": this.getMonth() + 1, //月份 
        "d+": this.getDate(), //日 
        "h+": this.getHours(), //小时 
        "m+": this.getMinutes(), //分 
        "s+": this.getSeconds(), //秒 
        "q+": Math.floor((this.getMonth() + 3) / 3), //季度 
        "S": this.getMilliseconds() //毫秒 
    };
    if (/(y+)/.test(fmt)) fmt = fmt.replace(RegExp.$1, (this.getFullYear() + "").substr(4 - RegExp.$1.length));
    for (var k in o)
    if (new RegExp("(" + k + ")").test(fmt)) fmt = fmt.replace(RegExp.$1, (RegExp.$1.length == 1) ? (o[k]) : (("00" + o[k]).substr(("" + o[k]).length)));
    return fmt;
}


function timestamp_format(timestamp, format){
	var that = new Date(timestamp * 1000);
	var o = {
	"M+" : that.getMonth()+1, //month
	"d+" : that.getDate(), //day
	"h+" : that.getHours(), //hour
	"m+" : that.getMinutes(), //minute
	"s+" : that.getSeconds(), //second
	"q+" : Math.floor((that.getMonth()+3)/3), //quarter
	"S" : that.getMilliseconds() //millisecond
	}
	if(/(y+)/.test(format)) format=format.replace(RegExp.$1,
	(that.getFullYear()+"").substr(4- RegExp.$1.length));
	for(var k in o)if(new RegExp("("+ k +")").test(format))
	format = format.replace(RegExp.$1,
	RegExp.$1.length==1? o[k] :
	("00"+ o[k]).substr((""+ o[k]).length));
	return format;
}



function timestamp_to_datetime_str(timestamp) {
	return timestamp_format(timestamp,'yyyy-MM-dd hh:mm:ss')

}
function GetDatetimeStr(AddDayCount) {
    var timestamp = new Date().getTime() / 1000
    return timestamp_to_datetime_str(timestamp)
}

function datetime_str_to_timestamp(s){
    return Date.parse(s.replace(/-/g,"/")) / 1000;
}


/*   datetime_str:'2013-08-22 17:43:24' ,  604800  */
function add_seconds_return_timestamp(datetime_str, seconds){
	var t = datetime_str_to_timestamp(datetime_str) + seconds;
	return t;
}
//hh:ss转秒数
function time_str_to_sec(sDate_str){
    var time_and_min = sDate_str.split(':')
    return parseInt(time_and_min[0])*3600 +  parseInt(time_and_min[1])*60
}
//秒数转hh:ss
function sec_to_time_str(iTimeSec){
    iTimeSec = parseInt(iTimeSec)
    var hours = parseInt(iTimeSec/3600)
    var min = parseInt((iTimeSec%3600)/60)
    hours = hours<10?'0' + hours : hours
    min = min<10?'0' + min : min
    return hours+':'+min
}

//短时间，形如 (13:04:06)
function isTime(str)
{
	var a = str.match(/^(\d{1,2})(:)?(\d{1,2})\2(\d{1,2})$/);
	if (a == null) { return false;}
	if (a[1]>24 || a[3]>60 || a[4]>60)
	{
	return false
	}
	return true;
}

//短日期，形如 (2008-07-22)
function strDate(str)
{
	var r = str.match(/^(\d{1,4})(-|\/)(\d{1,2})\2(\d{1,2})$/); 
	if(r==null)return false; 
	var d= new Date(r[1], r[3]-1, r[4]); 
	return (d.getFullYear()==r[1]&&(d.getMonth()+1)==r[3]&&d.getDate()==r[4]);
}

//长时间，形如 (2008-07-22 13:04:06)
function strDateTime(str)
{
	var reg = /^(\d{1,4})(-|\/)(\d{1,2})\2(\d{1,2}) (\d{1,2}):(\d{1,2}):(\d{1,2})$/; 
	var r = str.match(reg); 
	if(r==null)return false; 
	var d= new Date(r[1], r[3]-1,r[4],r[5],r[6],r[7]); 
	return (d.getFullYear()==r[1]&&(d.getMonth()+1)==r[3]&&d.getDate()==r[4]&&d.getHours()==r[5]&&d.getMinutes()==r[6]&&d.getSeconds()==r[7]);
}



function get_datetime_func(str) {
	if ( isTime(str) ) return isTime
	if ( strDate(str) ) return strDate
	if ( strDateTime(str) ) return strDateTime
}


function setSelectDate(sAddDayCount,eAddDayCount,is_edate)
{
    var sEle = $('[name="sdate"]')
    var eEle = $('[name="edate"]')

    sEle.attr('value',GetDateStr(sAddDayCount));
    eEle.attr('value',GetDateStr(eAddDayCount,is_edate));

}


function GetDateStr(AddDayCount,is_edate) {
    var dd = new Date();
    var new_date = dd.dateAdd('d',AddDayCount)
    if (is_edate) {
        return new_date.Format("yyyy-MM-dd 23:59:59")
    }
    return new_date.Format("yyyy-MM-dd 00:00:00")
}


function linebreaksbr(str){
	return str.toString().replace(/\n/g,'<br>')
}

jQuery.fn.outerHTML = function(s) {
  return (s) ? this.before(s).remove() : $("<Hill_man>").append(this.eq(0).clone()).html();
 }



//搜索某容器内的checkbox
function searchCheckbox(text,container,callback){
		var container = typeof container=="string" ? $('#'+container) : container
        container.find("input[type='checkbox']").each(function() {
            var This_checkbox = $(this)
            var This = This_checkbox.parent('label')
            var _html = This.html()
            var checked = This_checkbox.is(':checked')
            if (_html){
            _html = _html.substr(_html.indexOf('>')+1)
               if(text.length==0 || _html.indexOf(text)>=0 || text.search(','+_html+',')>=0){
                    This.show()
               }else{
                    if(!checked ){This.hide()}
               }
               
            }
            if (callback) {
            	callback(This_checkbox)
            }
        })
}

function searchTableCheckbox(text,tableId) {
		$('#' + tableId + ' tr').each(function(i,tr){
			var $tr = $(tr)
			var  innerStr= $tr.text()
			if(text.length==0 || innerStr.indexOf(text)>=0){ 
				$tr.show()
				searchCheckbox(text,$tr.find('td:last'))
				
			} else {
				$tr.hide()
			}
		})
	
}

//扩展日期格式
Date.prototype.format = function(format)
{
    //yyyy-MM-dd hh:mm:ss
    var o =
    {
        "M+" : this.getMonth()+1, //month
        "d+" : this.getDate(),    //day
        "h+" : this.getHours(),   //hour
        "m+" : this.getMinutes(), //minute
        "s+" : this.getSeconds(), //second
        "q+" : Math.floor((this.getMonth()+3)/3),  //quarter
        "S" : this.getMilliseconds() //millisecond
    }
    if(/(y+)/.test(format))
    format=format.replace(RegExp.$1,(this.getFullYear()+"").substr(4 - RegExp.$1.length));
    for(var k in o)
    if(new RegExp("("+ k +")").test(format))
    format = format.replace(RegExp.$1,RegExp.$1.length==1 ? o[k] : ("00"+ o[k]).substr((""+ o[k]).length));
    return format;
}


//阻止冒泡
function stopFunc(e){    
    e.stopPropagation?e.stopPropagation():e.cancelBubble = true;        
}


//根据元素id获取模版
window.get_tmpl = function(id){
    return document.getElementById(id).innerHTML
}
//返回渲染的模版
window.get_views = function(tmpl_id,obj){
	var data = {"w":window}
		data['data'] = obj

    return doT2.template(window.get_tmpl(tmpl_id))(data)
}

function removeParent(childEle){
	$(childEle).parent().remove()
}

// 本地json数据
var localJson = {
	get : function(key,default_obj){
		var json_str = localStorage.getItem(key)
		return json_str ? $.parseJSON(json_str) : default_obj
	},
	save:function(key,obj){
		var json_str = '';
		if (typeof obj == 'object'){
			json_str = JSON.stringify(obj)
		}
		localStorage.setItem(key,json_str)
	},
	additem:function(key,item){
		var item_list = this.get(key)
		item_list = $.isArray(item_list) ? item_list : []
		item_list.push(item)
		this.save(key,item_list)
	}
}

// 判断是否dom对象
var isDOM = ( typeof HTMLElement === 'object' ) ?
            function(obj){
                return obj instanceof HTMLElement;
            } :
            function(obj){
                return obj && typeof obj === 'object' && obj.nodeType === 1 && typeof obj.nodeName === 'string';
            }

/*
导出excel
 tableToExcel('channel_table', 'W3C Example Table')
*/
var tableToExcel = (function() {
     var uri = 'data:application/vnd.ms-excel;base64,'
        , template = '<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40"><head><!--[if gte mso 9]><xml><x:ExcelWorkbook><x:ExcelWorksheets><x:ExcelWorksheet><x:Name>{worksheet}</x:Name><x:WorksheetOptions><x:DisplayGridlines/></x:WorksheetOptions></x:ExcelWorksheet></x:ExcelWorksheets></x:ExcelWorkbook></xml><![endif]--></head><body><table>{table}</table></body></html>'
        , base64 = function(s) { return window.btoa(unescape(encodeURIComponent(s))) }
        , format = function(s, c) { return s.replace(/{(\w+)}/g, function(m, p) { return c[p]; }) }
      return function(table, name) {
        if (!table.nodeType) table = document.getElementById(table)
        var ctx = {worksheet: name || 'Worksheet', table: table.innerHTML}
        window.location.href = uri + base64(format(template, ctx))
      }
})()

$(document).ready(function() {
	// -- 繁简体 --
	doLanguageTypeChange();

})