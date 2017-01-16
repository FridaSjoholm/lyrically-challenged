$(function() {
      console.log("HEY YA")

  $(".form-search").on("ajax:success", function(e, data, status, xhr) {
    console.log("ajax call success")
    $('.f-pending-message').hide();
    $('#show-area').show();
    $('#show-area').html(data);
  });

  $(".form-search").on("ajax:beforeSend", function() {
    console.log("in beforeSend")
    $('#show-area').hide();
    $('.f-pending-message').show();
  });

//trying from scripts.js
      // $(window).load(function() {
      //     $('#pre-status').fadeOut();
      //     $('#st-preloader').delay(350).fadeOut('slow');
      // });

});
