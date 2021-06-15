$(window).resize(function(){
var userAgent = navigator.userAgent || navigator.vendor || window.opera;
if (/android/i.test(userAgent)) {
//debugger;
$('.app_btn').attr('href', "https://play.google.com/store/apps/details?id=com.docmode&hl=en_IN");
return "android"
}

// iOS detection from: http://stackoverflow.com/a/9039885/177710
if (/iPad|iPhone|iPod/.test(userAgent) && !window.MSStream) {
//debugger;
$('.app_btn').attr('href', "");
    return "iOS";
}
});

$('.close_section').click(function(){

$('.app_download').css('display' ,'none');
})
