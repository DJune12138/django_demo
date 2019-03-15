//http://datatables.net/plug-ins/pagination#bootstrap
$.extend( true, $.fn.dataTable.defaults, {
	"sDom": "<'row'<'col-sm-3'f><'col-sm-3'><'col-sm-6 datatable_toolbar'>>rt<'row'<'col-sm-2'i><'col-sm-2'l><'col-sm-8'p>>",
	"sPaginationType": "bootstrap",
	"oLanguage": {
		"sLengthMenu": "Display _MENU_ records"
	}
} );


/* API method to get paging information */
$.fn.dataTableExt.oApi.fnPagingInfo = function ( oSettings )
{
    return {
        "iStart":         oSettings._iDisplayStart,
        "iEnd":           oSettings.fnDisplayEnd(),
        "iLength":        oSettings._iDisplayLength,
        "iTotal":         oSettings.fnRecordsTotal(),
        "iFilteredTotal": oSettings.fnRecordsDisplay(),
        "iPage":          Math.ceil( oSettings._iDisplayStart / oSettings._iDisplayLength ),
        "iTotalPages":    Math.ceil( oSettings.fnRecordsDisplay() / oSettings._iDisplayLength )
    };
}
 
/* Bootstrap style pagination control */
$.extend( $.fn.dataTableExt.oPagination, {
    "bootstrap": {
        "fnInit": function( oSettings, nPaging, fnDraw ) {
            var oLang = oSettings.oLanguage.oPaginate;
            var oClasses = oSettings.oClasses;
            var fnClickHandler = function ( e ) {
                e.preventDefault();
                if ( oSettings.oApi._fnPageChange(oSettings, e.data.action) ) {
                    fnDraw( oSettings );
                }
            };
 
            $(nPaging).append(
                '<ul class="pagination">'+
                    '<li class="first disabled dotremove "><a href="#"><i class="'+oClasses.sPageButton+" "+oClasses.sPageFirst+'"></i>'+oLang.sFirst+'</a></li>'+
                    '<li class="prev disabled dotremove "><a href="#"><i class="'+oClasses.sPageButton+" "+oClasses.sPagePrevious+'"></i>'+oLang.sPrevious+'</a></li>'+
                    '<li class="next disabled dotremove "><a href="#"><i class="'+oClasses.sPageButton+" "+oClasses.sPageNext+'"></i>'+oLang.sNext+'</a></li>'+
                    '<li class="last disabled dotremove "><a href="#"><i class="'+oClasses.sPageButton+" "+oClasses.sPageLast+'"></i>'+oLang.sLast+'</a></li>'+
                    '<li class=" dotremove "><input id="datable-page-input" style="width:25px" type="text" ></li>'+
                '</ul>'
            );
            var els = $('a', nPaging);
            var nFirst = els[0],
                nPrev = els[1],
                nNext = els[2],
                nLast = els[3]
            var nInput = $('#datable-page-input', nPaging);
            oSettings.oApi._fnBindAction( nFirst, {action: "first"},    fnClickHandler );
            oSettings.oApi._fnBindAction( nPrev,  {action: "previous"}, fnClickHandler );
            oSettings.oApi._fnBindAction( nNext,  {action: "next"},     fnClickHandler );
            oSettings.oApi._fnBindAction( nLast,  {action: "last"},     fnClickHandler );
            nInput.bind('keyup',function(){
                var oPaging = oSettings.oInstance.fnPagingInfo();
                var page_num = this.value
                if (!isNaN(page_num) && page_num && page_num>0){
                    page_num = page_num<=oPaging.iTotalPages ? page_num: oPaging.iTotalPages
                    page_num = parseInt(page_num) - 1
                    console.dir(oPaging.iTotalPages)
                    if ( oSettings.oApi._fnPageChange(oSettings, page_num) ) {fnDraw( oSettings );}
                }
            })
        },
 
        "fnUpdate": function ( oSettings, fnDraw ) {
            var iListLength = 8;
            var oPaging = oSettings.oInstance.fnPagingInfo();
            var an = oSettings.aanFeatures.p;
            var i, j, sClass, iStart, iEnd, iHalf=Math.floor(iListLength/2);
 
            if ( oPaging.iTotalPages < iListLength) {
                iStart = 1;
                iEnd = oPaging.iTotalPages;
            }
            else if ( oPaging.iPage <= iHalf ) {
                iStart = 1;
                iEnd = iListLength;
            } else if ( oPaging.iPage >= (oPaging.iTotalPages-iHalf) ) {
                iStart = oPaging.iTotalPages - iListLength + 1;
                iEnd = oPaging.iTotalPages;
            } else {
                iStart = oPaging.iPage - iHalf + 1;
                iEnd = iStart + iListLength - 1;
            }
 
            for ( i=0, iLen=an.length ; i<iLen ; i++ ) {
                // Remove the middle elements
                $('li', an[i]).not('.dotremove').remove();
 
                // Add the new list items and their event handlers
                for ( j=iStart ; j<=iEnd ; j++ ) {
                    sClass = (j==oPaging.iPage+1) ? 'class="active"' : '';
                    $('<li '+sClass+'><a href="#">'+j+'</a></li>')
                        .insertBefore( $('li.dotremove:eq(2)', an[i]))
                        .bind('click', function (e) {
                            e.preventDefault();
                            oSettings._iDisplayStart = (parseInt($('a', this).text(),10)-1) * oPaging.iLength;
                            fnDraw( oSettings );
                        } );
                }
                // Add / remove disabled classes from the static elements
                if ( oPaging.iPage === 0 ) {
                    $('li.first,li.prev', an[i]).addClass('disabled');
                } else {
                    $('li.first,li.prev', an[i]).removeClass('disabled');
                }
 
                if ( oPaging.iPage === oPaging.iTotalPages-1 || oPaging.iTotalPages === 0 ) {
                    $('li.next,li.last', an[i]).addClass('disabled');
                } else {
                    $('li.next,li.last', an[i]).removeClass('disabled');
                }
            }
        }
    }
} );