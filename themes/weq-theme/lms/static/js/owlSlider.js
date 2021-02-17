$(document).ready(function() {

  $('.owl-carousel').owlCarousel({
    loop:true,
    margin:10,
    nav: true,
    navText: ['<i class="fa fa-arrow-circle-left" aria-hidden="true"></i>',
        '<i class="fa fa-arrow-circle-right" aria-hidden="true"></i>'],
    responsiveClass:true,
    responsive:{
        0:{
            items:1,
            nav:true
        },
        600:{
            items:3,
            nav:false
        },
        1000:{
            items:5,
            nav:true,
            loop:false
        }
    }
})

 
  var owl = $("#owl-demo");
  owl.owlCarousel();
 
  // Custom Navigation Events
  $(".next").click(function(){
    owl.trigger('owl.next');
  })
  $(".prev").click(function(){
    owl.trigger('owl.prev');
  })
 
});




