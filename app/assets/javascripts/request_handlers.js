$(function() {

//when ajax call made, but data not yet sent back
  //show the loading... message, hide the old results from the last query
    $(".form-search").on("ajax:beforeSend", function() {
      $('#show-area').hide();
      $('.f-pending-message').show();
    });

// when API calls successfully return data of filtered songs to show
  // hide the loading... message
  $(".form-search").on("ajax:success", function(e, data, status, xhr) {
    var $display = $('#show-area')
    $('.f-pending-message').hide();
    $display.show();
    $display.html(data);
    $('html, body').animate({
        scrollTop: $("#show-area").offset().top
    }, 'slow');
  });

  $(".feelings-search").on("ajax:success", function(e, data, status, xhr) {
    $('.f-pending-message').hide();
    $('#show-songs').show();
    $('#show-songs').html(data);
  });

  $(".feelings-search").on("ajax:beforeSend", function() {
    $('#show-songs').hide();
    $('.f-pending-message').show();
  });

// trying jquery ui
  $(document).tooltip({
    tooltipClass: "pop-it"
    })

});

// $('.selector').tooltip({
//         tooltipClass: "tooltip",
// });
// });




// to show dropdown selection for madlib forms in the carousel
$(".dropdown-menu li a").click(function(){
  var selText = $(this).text();
  $(this).parents('.btn-group').find('.dropdown-toggle').html(selText);
});



//these window.load eventHandlers were originally from the bootstrap template's scripts.js file
//commented out until to ready to be implemented again
// $(window).load(function() {
//     $('#pre-status').fadeOut();
//     $('#st-preloader').delay(350).fadeOut('slow');
// });
