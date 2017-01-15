$(function() {
  $(".form-search").on("ajax:success", function(e, data, status, xhr) {
    $('.f-pending-message').hide();
    $('#show-area').show();
    $('#show-area').html(data);
  });

  $(".form-search").on("ajax:beforeSend", function() {
    $('#show-area').hide();
    $('.f-pending-message').show();
  });
});
