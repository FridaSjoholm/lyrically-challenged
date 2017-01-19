var accessToken = "a95a813211b34525b38129bd4540a98f",
baseUrl = "https://api.api.ai/v1/",
$speechInput,
$recBtn,
recognition,
messageRecording = "Recording...",
messageCouldntHear = "I couldn't hear you, could you say that again?",
messageInternalError = "Oh no, there has been an internal server error",
record = 0,
title = 0,
desc = 0,
messageSorry = "I'm sorry, I don't have the answer to that yet.";

$(document).on("turbolinks:load", function() {
  console.log("readyyyy")
  $speechInput = $("#speech");
  $recBtn = $("#rec");

  $speechInput.keypress(function(event) {
    if (event.which == 13) {
      event.preventDefault();
      send();
    }
  });
  //Starts the recording session on click
  $recBtn.on("click", function(event) {
    switchRecognition();
    record = 1;
  });


function startRecognition() {
  recognition = new webkitSpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.onstart = function(event) {
    respond(messageRecording);
    updateRec();
  };
  recognition.onresult = function(event) {
    recognition.onend = null;

    var text = "";
    for (var i = event.resultIndex; i < event.results.length; ++i) {
      text += event.results[i][0].transcript;
    }

    setInput(text);
    stopRecognition();
  };
  recognition.onend = function() {
    respond(messageCouldntHear);
    stopRecognition();
  };
  recognition.lang = "en-US";
  recognition.start();
}
//stops recognition if it recognizes voice
function stopRecognition() {
  if (recognition) {
    recognition.stop();
    recognition = null;
  }
  updateRec();
}
function switchRecognition() {
  if (recognition) {
    stopRecognition();
  } else {
    startRecognition();
  }
}

function setInput(text) {
  $speechInput.val(text);
  console.log(text)
  send();
}

function updateRec() {
  $recBtn.text(recognition ? "Stop" : "Speak");
}

// Captures the phrase you say and sends it back as JSON data
function send() {
  var text = $speechInput.val();
  $.ajax({
    type: "POST",
    url: baseUrl + "query",
    contentType: "application/json; charset=utf-8",
    dataType: "json",
    headers: {
      "Authorization": "Bearer " + accessToken
    },
    data: JSON.stringify({query: text, lang: "en", sessionId: "6c968de0-dbae-44b0-ac5e-14f9cfc18130"}),
    success: function(data) {
      prepareResponse(data);
    },
    error: function() {
      respond(messageInternalError);
    }
  });
}

$('#rec').on("click", function() {
  $(".form-search").on("ajax:success", function(){
    var value = $("#speech").val();
    $.ajax({
      type: "GET",
      url: '/random_feelings_search',
      data: {text: value}
    }).done(function(response){
      $(".form-search").val('');
    })
  })
})

//Captures voice JSON data and turns it into a string
function prepareResponse(val) {
  var dataJSON = JSON.stringify(val, undefined, 2);
  spokenResponse = val.result.speech;
  respond(spokenResponse);
  debugRespond(dataJSON);

  // if (record == 1) {
  record = 0;
  console.log("record");
  callAction(dataJSON);
  // }
  // if (title == 1) {
  //   title = 0;
  //   console.log(title)
  //   console.log("title");
  //   $speechInput.val("");
  //   submitTitle(dataJSON);
  // }
  // if (desc == 1) {
  //   desc = 0;
  //   console.log(desc)
  //   console.log("desc");
  //   $speechInput.val("");
  //   submitDesc(dataJSON);
  // }
}
});
