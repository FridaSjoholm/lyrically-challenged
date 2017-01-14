$(document).ready(function() {
  $(".form-search").on("ajax:success", function(e, data, status, xhr) {
    $('.f-pending-message').hide();
    $('#show-area').html(data);
  });

  $(".form-search").on("ajax:beforeSend", function() {
    $('.f-pending-message').show();
  });
});
