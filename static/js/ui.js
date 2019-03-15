// 用户界面相关

/* 分页 */
function goPage(pageNum) {
	var pageUrl = document.location.href;
	pageUrl = pageUrl.replace(/page_num=\d+/, '')

	var _form = $("form:first")
	if (_form.attr('method') && _form.attr('method').toLowerCase() == 'post') {
		_form.append($('<input type="hidden" name="page_num" value="'+ pageNum+'">'))
		_form.submit();
	} else {
		if (pageUrl.indexOf("?") == -1) {
			pageUrl += "?"
		}
		if (pageUrl.substr(pageUrl.length - 1, 1) == "&") {
				pageUrl = pageUrl.substr(0, pageUrl.length - 1);
		}
		var url = pageUrl + "&page_num=" + pageNum;
		document.location.href = url;
	}

}

function change_page(ele){
	var pageNum = $(ele).val()
	if(!isNaN(pageNum) && pageNum){
		goPage(parseInt(pageNum))
	}
}
/*分页
@pageNum 当前页数
@pageSize 页条目数
@totalRecord 总条目数
*/
function pager_post(pageNum, pageSize, totalRecord) {
	var totalPage = parseInt(totalRecord / pageSize);
	if (totalRecord % pageSize != 0)
		totalPage++;

	var pageUrl = document.location.href;
	pageUrl = pageUrl.replace(/page_num=\d+/, '')
	if (pageUrl.indexOf("?") == -1)
		pageUrl += "?"

	if (pageUrl.substr(pageUrl.length - 1, 1) != "&" && pageUrl.substr(pageUrl.length - 1, 1) != "?")
		pageUrl += "&";

	var pagerHtml = "每页 <font color='red'>" + pageSize + "</font>条 共 <font color='red'>" + totalRecord + "</font>条记录&nbsp&nbsp";
	if (pageNum > 1){
		pagerHtml += "<a href='javascript:goPage(" + 1 + ");'>第一页</a>";
		pagerHtml += "<a href='javascript:goPage(" + (pageNum - 1) + ");'>上一页</a>";
	}
	var sPageNum = pageNum - 4;
	if (sPageNum < 1)
		sPageNum = 1;
	var ePageNum = sPageNum + 10;
	if (ePageNum > totalPage)
		ePageNum = totalPage;

	for (var i = sPageNum; i <= ePageNum; i++) {
		if (i == pageNum)
			pagerHtml += '<span>' + i + '</span>';
		else
			pagerHtml += "<a href='javascript:goPage(" + i + ");'>" + i + "</a>";
	}

	if (pageNum < totalPage){
		pagerHtml += "<a href='javascript:goPage(" + (pageNum + 1) + ");'>下一页</a>";
		pagerHtml += "<a href='javascript:goPage(" + totalPage + ");'>最后一页</a>";
	}
	if (pageNum && totalPage && pageNum > totalPage){
		goPage(parseInt(totalPage))
	}
	pagerHtml += '&nbsp共&nbsp' + totalPage + '&nbsp页&nbsp&nbsp'
	pagerHtml += '<input type="text" style="width:30px; margin:0px; padding:0px;" onblur="change_page(this)" value="" > ';

	$("#pager").html(pagerHtml);
}
/* 兼容 GET */
function pager(pageNum, pageSize, totalRecord) {
	pager_post(pageNum, pageSize, totalRecord)
}
// page end

var search_dbl_cache = {};
//搜索下拉框
function search_dbl_list(dbl_class_name, input_box_class_name) {
	var target = $("." + dbl_class_name);
	if(search_dbl_cache[dbl_class_name + '_is_change']){
		if(search_dbl_cache[dbl_class_name + '_is_change'])
			return;
	}
	var input_value = $("." + input_box_class_name).val();

	var list = [];
	if(input_value == ''){
		if(search_dbl_cache[dbl_class_name]){
		 	list = search_dbl_cache[dbl_class_name];
		 	target.html('');
		}
	}else{
		var add_to_cache = false;
		target.find('option').each(function() {
			var item = $(this);
			if(!search_dbl_cache[dbl_class_name]){
				search_dbl_cache[dbl_class_name] = [];
				add_to_cache = true;
			}
			if(add_to_cache){
				search_dbl_cache[dbl_class_name].push(item);
			}

			if (-1 != item.text().indexOf(input_value)){
				list.push(item);
			}
		});

		if(list.length == 0 && search_dbl_cache[dbl_class_name]){
			list = search_dbl_cache[dbl_class_name];
		}
		target.html('');
	}

	for(var i = 0 ; i < list.length;i++){
		var item = list[i]
		target.append(item);
		search_dbl_cache[dbl_class_name + '_is_change'] = true;
	}
	search_dbl_cache[dbl_class_name + '_is_change'] = false;
}



//datatable 扩展
(function($) {
	$.fn.dataTableExt.oApi.fnGetColumnData = function ( oSettings, iColumn, bUnique, bFiltered, bIgnoreEmpty ) {
	    // check that we have a column id
	    if ( typeof iColumn == "undefined" ) return new Array();
	    // by default we only want unique data
	    if ( typeof bUnique == "undefined" ) bUnique = true;
	    // by default we do want to only look at filtered data
	    if ( typeof bFiltered == "undefined" ) bFiltered = true;
	    // by default we do not want to include empty values
	    if ( typeof bIgnoreEmpty == "undefined" ) bIgnoreEmpty = true;
	    // list of rows which we're going to loop through
	    var aiRows;
	    // use only filtered rows
	    if (bFiltered == true) aiRows = oSettings.aiDisplay;
	    // use all rows
	    else aiRows = oSettings.aiDisplayMaster; // all row numbers
	    // set up data array
	    var asResultData = new Array();
	    for (var i=0,c=aiRows.length; i<c; i++) {
	        iRow = aiRows[i];
	        var aData = this.fnGetData(iRow);
	        var sValue = aData[iColumn];
	        // ignore empty values?
	        if (bIgnoreEmpty == true && sValue.length == 0) continue;
	        // ignore unique values?
	        else if (bUnique == true && jQuery.inArray(sValue, asResultData) > -1) continue;
	        // else push the value onto the result data array
	        else asResultData.push(sValue);
	    }
	    return asResultData;
	}
	//增加select框
	$.fn.dataTableExt.oApi.fnAddSelect = function(oSettings,aColumnIndexs) {
		var oDatatable = this
		aColumnIndexs = aColumnIndexs?aColumnIndexs:[]
		function fnCreateSelect( aData )
		{
		    var r='<select><option value=""></option>', i, iLen=aData.length;
		    for ( var i=0 ; i<iLen ; i++ ) {
		    	var _val = aData[i].replace(/<[^>]+>|\r|\n|\t|\s*/g,"")
		        r += '<option value="'+_val+'">'+_val+'</option>';
		    }
		    return r+'</select>';
		}
		var tds_html = ''
		this.find('thead th').each(function(i,ele){
			tds_html += '<td class="datatable-select-td"></td>'
		})
		this.find('thead').after('<thead><tr>' + tds_html +'</tr></thead>')
		this.find('.datatable-select-td').each( function ( i ) {
				if ($.inArray(i,aColumnIndexs) >= 0 || aColumnIndexs.length == 0) {
			        this.innerHTML += fnCreateSelect( oDatatable.fnGetColumnData(i) );
				     $('select', this).change( function () {
				             oDatatable.fnFilter( $(this).val(), i );
				     });
				}
	    } );

	}
}(jQuery));

// 设置input值
function inputText(inputName, inputValue) {
	$("input[name='" + inputName + "']").val(inputValue);
}

/*jquery扩展 dialog*/
function myDialog(op,height){
		//var _top = "45%"
		if (typeof op=="object") {
			if (top.location != self.location) {
		    	var __top = parent.document.documentElement.scrollTop || parent.document.body.scrollTop
		    	_top = parseInt(__top) + 100
		    	op = $.extend({"top":_top},op);
	    	}


    	} else{
    		op = {"content":op,"fixed":true,top:"25%"}
    	}
    	console.dir(op)
    	var _dialog = art.dialog(op)
    	return _dialog
}

(function($) {
	$.fn.extend({
		/*dialog*/
		"dialog":function(op) {
			if ('close'== op) {
				//art.dialog.list[this.attr('id')].close()
				return
			}

			op = $.extend({
			    content: this[0],
			    id: $(this).attr('id'),
			}, op);
			return  myDialog(op,$(this).height()).show()
		}
    });
})(jQuery);
$.dialog = myDialog

$(document).on('click','.dialog',function(){
	var follow = $(this).attr('follow') ? this : false
	console.dir(follow)
	var _dialog = $.dialog({id: this.href,title: $(this).text(),follow:follow});
	$.ajax({
	    url: this.href,
	    success: function (data) {
	        _dialog.content(data);
	    },
	    cache: false
	});

	//artDialog.load(this.href,{title: $(this).text()},false);
	return false
}).on('click','.openDialog,opendialog',function(e){
	var This = $(this)
	var url = This.attr('url') ? This.attr('url') : This.attr('href')
	art.dialog.open(url,{title:$(this).text()})
	stopFunc(e)
	return false
})


function enfoldment(id){
		$('#'+id).toggleClass('enfoldment');
}

// checkbox 颜色
function change_checkbox_background(eles){
	eles = eles?eles:$(':checkbox')
    eles.each(function(i,ele){
    	var _e = $(ele)
    	if (_e.is(':checked')){
    		_e.parent('label').addClass('checked')
    	} else {
    		_e.parent('label').removeClass('checked')
    	}
    })
}
$(document).on('click','label>:checkbox',function(){
	change_checkbox_background($(this))
})



/* POST打开新窗口
@url 地址
@name 窗口名
@fWidth 窗口宽系数 0.5
@fHeight 窗口高系数 0.5
@Data POST 的数据 aa=aa&aa=bb
*/
function openwindow(url,name,fWidth,fHeight,Data)
 {
  var url;                                 //转向网页的地址;
  var name;                           //网页名称，可为空;
  var  iWidth=parseInt(window.screen.availWidth * fWidth),                          //弹出窗口的宽度;
  	   iHeight=parseInt(window.screen.availHeight * fHeight)
  var  iTop = parseInt((window.screen.availHeight-iHeight)/2),      //获得窗口的垂直位置;
       iLeft = parseInt((window.screen.availWidth-iWidth)/2);           //获得窗口的水平位置;

  var Window_obj = window.open(url,name,'height='+iHeight+',,innerHeight='+iHeight+',width='+iWidth+',innerWidth='+iWidth+',top='+iTop+',left='+iLeft+',scrollbars=yes');
    //,toolbar=no,menubar=no,scrollbars=yes,resizeable=no,location=no,status=no');
  if (Data) {//Post一个新窗口
  	//url = Data ? 'about:blank' : url;
	var tempForm = document.createElement("form");
	tempForm.id = "tempForm1"
	tempForm.method = "post"
	tempForm.action = url
	tempForm.target = name;
	//console.dir(Data)
	Data += '&_Random=' + parseInt( Math.random()*1000000000000 )
	var kv = Data.split('&')
	for (var i in kv){
		var _kv = kv[i].split('=')
  		var hideInput = document.createElement("input");
  		hideInput.type = "hidden";
  		hideInput.name = decodeURIComponent(_kv[0])
        if (_kv[1]) {
            hideInput.value = decodeURIComponent(_kv[1].replace(/\+/g, ' '))
        } else {
            hideInput.value = decodeURIComponent(_kv[1])
        }
  		tempForm.appendChild(hideInput);
	}
        document.body.appendChild(tempForm);
        tempForm.submit();
        // document.body.removeChild(tempForm);
    }
}



/*全选*/
$(document).on('click','[checkbox-area]',function(){
		var This = $(this),
			_checked = This.is(':checked')
		var  areaId = This.attr('checkbox-area')
		var checkbox_cont = $('.'+areaId+':visible')
		checkbox_cont = checkbox_cont.length>0 ? checkbox_cont : $('#'+areaId)
		var checkboxs = checkbox_cont.find(':checkbox:visible')

		checkboxs.each(function(i,ele){
			var checkboxEle = $(ele)

			checkboxEle.prop('checked', _checked);
			change_checkbox_background(checkboxEle)
		})
}).on('click','.openwindow',function(){
	var This = $(this)
	var url = This.attr('href'),
		data = This.attr('data'),
		name = This.attr('windowname'),
		fWidth = This.attr('fWidth'),
		fHeight = This.attr('fHeight')
	openwindow(url,name,fWidth,fHeight,data)
	return false
})

// 随机验证码确认
function confirmRandom(text){
	var  random = parseInt(Math.random()*1000)
	text = text ? text : ''
	return prompt(text + '  请输入:'+random) == random
}

function check_input_empty(ele){
	var ele = ele ? ele : $('body')
	var check_empty_eles = ele.find('.not-empty')
	var is_check_done = true
	if (check_empty_eles.length>0) {
		for(var i=0;i<check_empty_eles.length;i++){

			if(!check_empty_eles[i].value){
				inputTooltip(check_empty_eles[i],'<b class="red">不能为空值!</b>',3000)
				check_empty_eles[i].focus();
				is_check_done = false
				break
			}
		}
	}
	return is_check_done
}


$(document).on('focus','.Wdate',function(){
		WdatePicker({
			dateFmt : 'yyyy-MM-dd HH:mm:ss'
		})
}).on('focus','.Wdate1',function(){
		WdatePicker({
			dateFmt : 'yyyy-MM-dd'
		})
}).on('focus','.Wdate2',function(){
		WdatePicker({
			dateFmt : 'HH:mm:ss'
		})
}).on('focus','.Wdate3',function(){
		WdatePicker({
			dateFmt : 'HH:mm'
		})
}).on('focus','.Wdate4',function(){
		WdatePicker({
			dateFmt :  'yyyy-MM-dd HH:mm:00'
		})
}).on('focus','.WdateY',function(){
	WdatePicker({
		dateFmt :  'yyyy-01-01'
	})
}).on('focus','.WdateM',function(){
	WdatePicker({
		dateFmt :  'yyyy-MM-01'
	})
}).on('focus','.WdateD',function(){
	WdatePicker({
		dateFmt :  'yyyy-MM-dd'
	})
}).on('focus','.WdateH',function(){
	WdatePicker({
		dateFmt :  'HH:mm'
	})
}).on('focus','.WdateW',function(){
	WdatePicker({
		dateFmt :  'yyyy-MM-dd',
		disabledDays:[2,3,4,5,6,0]
	})
}).on('click','.ask',function(){
	return confirm("确认进行此操作吗 ?")
}).on('click','.del,.remove,.delete',function(){
	return confirmRandom('确认删除吗?')
})





var selectId = 0
$(document).ready(function() {


	 //select增加svalue为默认选择
	$("select[svalue]").each(function() {
			target = $(this);
			var value = target.attr('svalue');
			if(value == ''){
				return;
			}
			target.find('option').each(function(){
				o = $(this);
				if (value == o.val()){
					o.attr('selected', true);
					return;
				}
			})
	});



    //顶条快捷添加模块菜单
	// $('.bar').contextmenu(function(e){
	// 	var rightmenu = $('#rightmenu')
	// 	if (rightmenu.length<=0) {
	// 		rightmenu = $('<div>',{"class":"rightmenu","id":"rightmenu","html":"","click":function(e){stopFunc(e)}})
	// 		var add_module_btn = $('<a>',{"html":"添加模块","class":"btn btn-sm","click":function(e){
	// 			art.dialog.open('/system/menu/menu_edit?url='+window.location.href.split(window.location.host,2)[1]+'&name='+document.title,{ width: '50%',height:"95%",title:$(this).text()})
	// 			rightmenu.hide()
	// 		}})

	// 		rightmenu.append(add_module_btn)
	// 		$('body').append(rightmenu)
	// 		$(document).click(function(){
	// 			rightmenu.hide()
	// 		})
	// 	}
	// 	if(e.target==this){
	// 		rightmenu.css("top",e.pageY)
	// 		rightmenu.css("left",e.pageX)
	// 		rightmenu.show()
	// 		return false
	// 	}
	// })


	// -- datatable --
	$('.datatable').each( function(index, ele) {
			var tableObj = $(ele)
		 	var opt = {
					//"sScrollY": '200px',//document.documentElement.clientHeight*0.6 + 'px',
					//"bScrollCollapse": true,
					//"sScrollX": "100%",
                    //"sScrollXInner": "100%",
                    "bSortClasses":false,
					"bStateSave": false,
					"bProcessing": true, //是否显示正在处理的提示
					"iDisplayLength":-1,//默认每页显示的记录数
					"bPaginate": false, // 是否使用分页
					"aLengthMenu":[50,100,1000],
					"bAutoWidth": false,//列的宽度会根据table的宽度自适应
					//"bSortClasses":true,
					"bLengthChange": true,//分页栏
					"oSearch":{
						"sSearch": "",//默认的框文字
						"bRegex":true,//支持正则搜索
					},
					"bInfo": true,
					 "oLanguage": {
					 "sSearch": "筛选:",//
					 "sZeroRecords": "没有匹配记录",
					  "sInfo":'当前 _START_ - _END_ 条 共 _TOTAL_ 条',
					  "sInfoFiltered": "(从 _MAX_ 条记录中过滤)",
					  "sLengthMenu": "每页显示 _MENU_条",
					  "sProcessing":"正在加载数据...",
					  "sInfoEmpty": "",
					  "oPaginate": {
                        "sFirst": "首页",
                        "sPrevious": "前一页",
                        "sNext": "后一页",
                        "sLast": "尾页"
                    	}

					 },
					 "aoColumnDefs":[],
					 "aaSorting":[] //默认不排序
				}
			var checkboxIndex = tableObj.find('th>:checkbox').index()//checkbox的列不排序
			if(checkboxIndex>=0) {
				opt["aoColumnDefs"].push(
							{
		           			"bSortable": false,
		            		"aTargets": [checkboxIndex]
		        			}
		        )
			}
			opt["bInfo"] = tableObj.attr("data-bInfo")=='false' ? false : true
			var oDatatable = tableObj.dataTable(opt)
			var toolbarId = tableObj.attr('data-toolbar')
			toolbarId = toolbarId ? toolbarId : 'datatable_toolbar'
			toolbarEle = $('#'+toolbarId)
			toolbarEle.appendTo(oDatatable.parent().find('.datatable_toolbar'))
			// toolbarEle.find('[href]').click(function(){
			// 	//alert(tableObj.find('[name]').serialize())

			// })
		 	var group_by_index = tableObj.attr('data-group-by-index')//分组
		 	if (group_by_index) {
		 		oDatatable.fnAddSelect($.parseJSON(group_by_index))
		 	}
    });

	//树表格
	$(".treetable").treetable(
		{ expandable: true ,clickableNodeNames:false}
	).on('dblclick','tbody>tr',function(){
		var This = $(this)
		var tt_id = This.attr("data-tt-id")
		var action = This.find('[title="Expand"]').length>0?"expandNode":"collapseNode"
		This.closest('.treetable').treetable(action,tt_id)
	})

	// table 选中
	$('.datatable,.treetable').on("mousedown", "tbody>tr", function(e) {
	  $(".selected").not(this).removeClass("selected");
	  var This = $(this)

	  selectId = 0
	  This.toggleClass("selected");
	  if (This.hasClass('selected')) {
	  	selectId = This.attr('trid') ? This.attr('trid') : This.find(':checkbox').val()
	  }

	  // if (!$(e.target).is(':checkbox')) {
	  // 	This.find(':checkbox').click();
	  // }
	})


	$('.submit').click(function(){
		$('form:first').submit()
	})
	change_checkbox_background()

	/* 选择框 */
	$(".chosen-select").chosen();

	$('.table-menu a').mousemove(function(event) {
		$(this).addClass('active')
		$('.table-menu a').not(this).removeClass('active')
	});


	$('.spinner1').ace_spinner({value:0,min:0,max:200,step:10, btn_up_class:'btn-info' , btn_down_class:'btn-info'})
	.on('change', function(){
		//alert(this.value)
	});

	// 下拉菜单悬停
	$('.dropdown-menu-not-hide').click(function(e){e.stopPropagation()})
})



/*输入框增加下拉选择
	input 控件属性
	@select_key 获取字典列表的key
	@value_forat 自动填值时额外的格式
*/
function SelectInput(){
		var This = this
		var  ignore_keys = ['img_path_format',] //特殊用途的key
		var  _div = $("#follow_div")

		/*
		初始化和绑定事件
		*/
		this.init = function(){
				//初始化,增加一个跟踪控件的div
				if (_div.length==0){
				     _div = $('<div>',{"id":"follow_div"})
				     $(document.body).append(_div)
				     //外层点击事件
					 $('body').click(function(evt) {
					    if($(evt.target).parents("#follow_div").length==0 &&
					        !$(evt.target).attr('select-key') && evt.target.id != "follow_div") {
					        $('#follow_div').hide();
					    }
					 });
				 }

				$('[select_key]').each(function(i,ele){
					var _This = $(ele)
					var _interface_key = _This.attr('select_key')
					_This.removeAttr('select_key')
					_This.attr('select-key',_interface_key)
					// _This.focus(function(event) {
					// 	This.show_div($(this),_This)

					// });
					// _This.keyup(function(event) {
					// 	This.search(_This.val())
					// });
				})



				$(document).on('focus','[select-key]',function(){
					This.show_div($(this),$(this))

				}).on('keyup','[select-key]',function(){
					This.search($(this))
				})


				/* 初始化 chosen控件添加选项*/
				function chosenInit(k_v,ele) {
					var textFormat = ele.attr('value_format')
					for(var k in k_v){
						if ($.inArray(k,ignore_keys)>=0 || k==''){continue}
						var text = k_v[k]

						if (textFormat) {
							text = textFormat.replace(/__key__/g,k).replace(/__value__/, k_v[k])
						}
						ele.append("<option value='"+k+"'>" + text +"</option>");

					}
					var default_value = ele.attr('data-default-value')
					ele.attr('chosen-key',ele.attr('chosen_key'))
					ele.removeAttr('chosen_key')
					if (default_value) {
						try{
							default_value = $.parseJSON(default_value)
						}catch(e){
							console.dir(default_value)
						}
						ele.val(default_value)
					}
					ele.chosen({"search_contains":true})
				}

				$('select[chosen_key]').each(function(i,ele){
					var chosenSelectEle = $(ele)
					var select_key = chosenSelectEle.attr('chosen_key')
					This.get_dict(select_key,chosenSelectEle,chosenInit)
				})

				function tagInit(k_v,ele) {
					ele.attr('tag-key',ele.attr('chosen_key'))
					ele.removeAttr('tag_key')
					//we could just set the data-provide="tag" of the element inside HTML, but IE8 fails!
					var tag_input = ele;
					var values = []
					$.each(k_v,function(k,v){
							values.push(v)
					})
					console.dir(values)
					if(! ( /msie\s*(8|7|6)/.test(navigator.userAgent.toLowerCase())) )
					{
						tag_input.tag(
						  {
							placeholder:tag_input.attr('placeholder'),
							//enable typeahead by specifying the source array
							source: values,//defined in ace.js >> ace.enable_search_ahead
						  }
						);
					}
					else {
						//display a textarea for old IE, because it doesn't support this plugin or another one I tried!
						tag_input.after('<textarea id="'+tag_input.attr('id')+'" name="'+tag_input.attr('name')+'" rows="3">'+tag_input.val()+'</textarea>').remove();
						//$('#form-field-tags').autosize({append: "\n"});
					}
				}


				$('input[tag_key]').each(function(i,ele){
					var tagSelectEle = $(ele)
					var select_key = tagSelectEle.attr('tag_key')
					This.get_dict(select_key,tagSelectEle,tagInit)
				})


		}
		this.search = function($ele){
			var value = $ele.val()
			var is_multiple = $ele.attr('data-multiple')

			_div.find('.select-a').each(function(i, _ele) {
				var __ele = $(_ele)
				 if (__ele.text().indexOf(value)>=0 || is_multiple ){
				 	$(__ele).parent('li').show()
				 }else{
				 	$(__ele).parent('li').hide()
				 }
			});


		}
		this.show_div = function(follow_obj,input_obj){
			//if(_div.is(":hidden")){
				var x =  follow_obj.offset();
				_div.css({"left":x.left,"top":x.top+follow_obj.outerHeight()-1,"min-width":input_obj.innerWidth()})
				var _key = input_obj.attr('select-key')
				_div.html('载入中...')
				This.get_dict(_key,input_obj,This.padding_div)
				_div.show()
			//}
		}

		this.padding_div = function(json,input_obj ){
			var contains = _div

		    if (contains.find('a').length==0) {
		    	contains.html('')
		    	var is_multiple = input_obj.attr('data-multiple') == 'true'
			    var _ul = $('<ul>',{"class":"select-ul"})
			    //if (is_multiple) {
			    	contains.append($('<input>',{"type":"text","class":"input-small","placeholder":"搜索","keyup":function(){
			    		This.search($(this))
			    	}}))
			    //}
			    contains.append(_ul)
			    var _img_url_format = ''
			    var value_format = input_obj.attr('value_format')?input_obj.attr('value_format'):'__key__'
			    var text_format =  input_obj.attr('text_format')?input_obj.attr('text_format'):'__value__(__key__)'
			    if (json.img_path_format) {
			    	_img_url_format = '/static/img/' + json.img_path_format
			    }
			    var _key_list = [];
				$.each(json, function(key, val) { _key_list.push(key);  });
				_key_list.sort()
		        for(var _i in _key_list){
		        	var k = _key_list[_i]
		        	var _li = $('<li>',{"class":"select-li"})
		        	if ($.inArray(k,ignore_keys)>=0 || k==''){
		        		continue
		        	}

		        	var _value = json[k]
		        	var _invalue = value_format.replace(/__key__/g,k )
		        	var test = text_format.replace(/__key__/g,k).replace(/__value__/g,_value)
		        	var  _a = $('<a>',{"html":test,"href":"javascript:void(0)","value":k,invalue:test,"title":k+'('+_value+')',"class":'select-a'})
		        	_a.click(function(event) { //点击事件

		        		var select_value = $(this).attr('invalue')
		        		if (is_multiple) {
		        			var invalue = input_obj.val()
		        			if (invalue.match(/,$/) || !invalue) {
		        				invalue += select_value
		        			} else {
		        				invalue += ',' + select_value
		        			}
		        			select_value = invalue
		        		}

		                input_obj.val(select_value)
		                do_change(select_value,input_obj)
		                contains.hide()
		        	})
		        	if (_img_url_format){
		        		_a.mouseenter(function(event) {
		        			var This = $(this)
			        		var item_img_url = _img_url_format.replace(/__key__/g,This.attr('value'))
			        		var _img = $('<img>',{"src":item_img_url,"alt":This.text(),"class":"select-img","error":function(){this.src='/static/img/err.png'}})
			        		This.after(_img)
		        		});
		        		_a.mouseout(function(){
		        			$(this).next('img').remove()
		        		})
		        	}
		        	_li.append(_a)
		        	_ul.append(_li)
		        }
	        }
	        This.search(input_obj)
		}
		//获取字段到a标签 callback(json,input_obj )
		this.get_dict = function(key,input_obj,callback){
							var k_v = null
							if (key.indexOf('{')>=0) {
								try{
									k_v = $.parseJSON(key)
								}
								catch(e){
									console.dir(e)
								}
							} else {
								var built_data = input_obj.data(key)
								    k_v = built_data?built_data:_div.data(key)
							}

							if (k_v){
								callback(k_v,input_obj)
							}else{
								var _url = '/log/dict/interface?key='+key
								$.getJSON(_url, {}, function(json) {
										_div.data(key,json)
										callback(json,input_obj )
								});
							}
	    }
}

function do_change(){

}

function inputTooltip(ele,text,time){
	var This = $(ele)
	var offset = This.position()
	var span = This.next('.input-tooltip')

	if (span.length==0) {
		span = $('<span>',{"style":"line-height:2em;border-radius: 4px;box-shadow: 2px 2px 3px #969696;cursor: pointer;background-color: white; padding: 0 5px 0 5px;z-index: 999999999;border: 1px solid #AAAAAA;position:absolute;font-weight: bold;","html":"","class":"input-tooltip","click":function(){$(this).hide()}})
		This.after(span)
	}
	var h = 30
	span.css({"left":offset.left,"top":offset.top-h})
	//span.css({"left":offset.left,"top":offset.top-This.innerHeight()-1,"height":This.innerHeight()})
	span.html(text)
	if (text) {
		span.show()
		if (time) {
			span.fadeOut(time)
		}
	} else {
		span.hide()
	}

	return span
}

function make_toolip(ele,tooltipText,time){

			var tooltipEle = inputTooltip(ele,tooltipText,time)
			if (tooltipText) {
				tooltipEle.css({'color':'red'})
			} else {
				tooltipEle.hide()
			}
}

function check_json(ele){
		    var This = $(ele)
		    var tooltipText = ''
		    try{
		         var j_data = $.parseJSON(This.val())
		         tooltipText = typeof j_data == 'object' ? '' : '错误的json格式'
		    }catch(e){
		    	tooltipText = '错误的json格式'
		    }
		    make_toolip(ele,tooltipText)
}



$(document).on('blur','.input-number',function(){
	var tooltipText = ''
	var $this = $(this)
	var value = $this.val()

	if (isNaN(value) || value.length==0) {
		tooltipText = '输入的不是数字 !'
		//alert(tooltipText)
		$this.val( value.replace(/[^\d-\.]+/g,'') )
		//this.focus();
	}

	value = parseInt(value)
	if (value>10000) {
			tooltipText = parseInt(value / 10000) + ' 万'
	}
	make_toolip(this,tooltipText,5000)

}).on('keyup','.check_json,.check-json,.textarea-json',function(){
	$(this).attr('placeholder','只能JSON格式')
	check_json(this)

}).on('blur','.letter,.input-letter',function(){

	make_toolip(this,this.value.replace(/[a-zA-Z-_]+/g,'')!='' ? '输入的不是纯字母!' : '')
})



var select_input = new SelectInput()

$(document).ready(function() {
	select_input.init()
	change_checkbox_background()
})
