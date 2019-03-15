//---滚动到顶部固定 Edit:JeanChen 15:44 2012/5/29
$.fn.scrollToFixed=function(b,c){
	var a=function(e,d,f){
	$(window).scroll(function(){
		if(document.body.scrollTop){
				var g=document.body.scrollTop
			}else{
				var g=document.documentElement.scrollTop
			}
		e.attr("d",g);
		e.attr("t",d);
		if(!d){
			//d=g+document.getElementById(e.attr("id")).getBoundingClientRect().top-26}if(g>d){
			d=g+document.getElementById(e.attr("id")).getBoundingClientRect().top-2}if(g>d){
			e.addClass(f)
			}else{
				if(e.hasClass(f)){
					e.removeClass(f)
				}
			}
			}
		)};
		return $(this).each(function(){
		a($(this),b,c)
		}
)};

//---智能浮动层
$.fn.smartFloat=function(){
	var a=function(b){
		var c=b.position().top;
		pos=b.css("position");
		$(window).scroll(function(){
			//var d=$(this).scrollTop()-144;
			var d=$(this).scrollTop()-2;
			if(!window.XMLHttpRequest){
				//d=d-28
				d=d-1
			}if(d>c){
				if(window.XMLHttpRequest){
					b.css({
						position:"fixed",
						//top:26
						top:0
					})
				}else{
					b.css({
						top:d
					})
				}
				}else{
					b.css({
						position:"absolute",
						top:c
					});

					//$(".gbuy_content").css({"padding-top":48})
				}
				}
		)};
		return $(this).each(function(){
			a($(this))
			}
		)
};



// 锚点起点部分：$(".goBuy").anchorGoWhere({target:1});  1为纵向 2为横向
// <a href="#Buy" class="goBuy">菜单一</a>
// <legend id="Buy">菜单一的内容</legend>

 jQuery.fn.anchorGoWhere = function(options){
     var obj = jQuery(this);
     var defaults = {target:0, timer:1000};
     var o = jQuery.extend(defaults,options);
     obj.each(function(i){
         jQuery(obj[i]).click(function(){
             var _rel = jQuery(this).attr("href").substr(1);
             switch(o.target){
                 case 1: 
                     var _targetTop = jQuery("#"+_rel).offset().top;
                     jQuery("html,body").animate({scrollTop:_targetTop},o.timer);
                     break;
                 case 2:
                     var _targetLeft = jQuery("#"+_rel).offset().left;
                     jQuery("html,body").animate({scrollLeft:_targetLeft},o.timer);
                     break;
             }
             return false;
         });                  
     });
 };