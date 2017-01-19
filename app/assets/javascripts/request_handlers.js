$(document).on("turbolinks:load", function() {

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


//For popover when hover over Details
  $(document).tooltip({
    tooltipClass: "pop-it"
  });

//For pagination
  $("#show-area").on("ajax:success", ".see-more a", function(e, data, status, xhr) {
    $(".see-more").hide()
    $("#show-area").append(data);
  });

  // setup graphic EQ
  $( "#eq > span" ).each(function() {
    console.log("in slider thing");
    // read initial values from markup and remove that
    var value = parseInt( $( this ).text(), 10 );
    $( this ).empty().slider({
      value: value,
      range: "min",
      animate: true,
      orientation: "vertical"
    });
  });


});//end of document on turbolinks load


// //for sliders_search
// $( function() {
//   $( "#sliderrr" ).slider();
// } );



// } );




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
