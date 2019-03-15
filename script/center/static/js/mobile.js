

// 手机适配
var userAgent = navigator.userAgent;
var isIos = userAgent.match(/i[^;]+;( U;)? CPU.+Mac OS X/) != null;
if(isIos){

	var search_list = window.location.hash.match(/#hw=(\d+),(\d+)/);

	document.getElementsByTagName("head")[0].innerHTML += '<meta name="viewport" content="target-densitydpi=device-dpi, width=700, user-scalable=no"/>';
	
}else{
	var ratio = window.devicePixelRatio;
	if (ratio > 1.5) {
		document.getElementsByTagName("head")[0].innerHTML += '<meta name="viewport" content="target-densitydpi=240,initial-scale=1.0"/>';
	}else if(ratio < 1){
		document.getElementsByTagName("head")[0].innerHTML += '<meta name="viewport" content="target-densitydpi=160,initial-scale=1.0"/>';
	}
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

function add_args(){
	var args = getArgs()
	var search_params = location.search
	if (args.hasOwnProperty('sid')){
		var changeTags = {"a":"href","form":"action","iframe":"src"}
		for (var key in changeTags){
			var tagName = key
			var attrName = changeTags[key]
			var Objs = document.getElementsByTagName(tagName)
			for(var i=0;i<Objs.length;i++){
				var obj = Objs[i]
				var link = obj[attrName]
				if (link){
					if (link.indexOf('?')>0){
						search_params = search_params.replace(/?/g,'&')
					}
					obj[attrName] += search_params
				}
			}
		}
	}
}
window.onload = function(){
	add_args()
}