"use strict";
(function() {

  const WIDTH = 500;
  const HEIGHT = 375;
  const HOST = "http://gazecapture455.westus2.cloudapp.azure.com:5000/model"

  let timer;

  window.addEventListener("load", init);

  function init() {
    let canvas = document.createElement('canvas');
    canvas.width  = WIDTH;
    canvas.height = HEIGHT;
    let ctx = canvas.getContext("2d");

    turnCamOn();
    // TODO: fill site with junk or random photos (so we can scroll the page)
    // TODO: also add instructions/descriptions for the buttons
    $("camButton").addEventListener("click", toggleCamera);
    $("captureButton").addEventListener("click", function() {
      processImage(canvas, ctx);
    });
    $("scrollButton").addEventListener("click", function() {
      processStreamOfImages(canvas, ctx);
    });
  }

  function toggleCamera() {
    if ($("camButton").classList.contains("camButtonOn")) {
      turnCamOn();
      $("captureButton").disabled = false;
      $("camButton").innerText = "Turn Webcam Off";
      $("scrollButton").disabled = false;
    } else {
      $("webcam").srcObject.getTracks()[0].stop();
      $("captureButton").disabled = true;
      $("camButton").innerText = "Turn Webcam On";
      $("scrollButton").disabled = true;
    }
    $("camButton").classList.toggle("camButtonOn");
  }

  function turnCamOn() {
    let video = $("webcam");

    if (navigator.mediaDevices.getUserMedia) {
      navigator.mediaDevices.getUserMedia({ video: true })
        .then(function (stream) {
          video.srcObject = stream;
          let mediaStreamTrack = stream.getVideoTracks()[0];
          video.play();
        })
        .catch(function (e) {
          alert("Something went wrong!");
        });
    }
  }

  function processImage(canvas, ctx) {
    // capture the current image from the webcam
    let img = document.getElementById("webcam");
    ctx.drawImage(img, 0, 0, WIDTH, HEIGHT);
    let jpegFile = canvas.toDataURL("image/jpeg");

    let params = new FormData();
    params.append("image", jpegFile);

    // sends the image to the backend to be evaluated with the model
    fetch(HOST, {method: "POST", body: params})
      .then(checkStatus)
      .then(resp => resp.text())
      .then(processCoordinates)
      .catch(console.log);
  }

  function processCoordinates(response) {
    // TODO: change to display coords (dot on screen at the position)
    $("debug").innerText = response
  }

  function processStreamOfImages(canvas, ctx) {
    let scrollBtn = $("scrollButton");
    if (timer != null) {
      clearInterval(timer);
      timer = null;
      scrollBtn.innerText = "Click to Scroll";
    } else {
      scrollBtn.innerText = "Stop Scrolling";
      timer = setInterval(function() {
          processImage(canvas, ctx);
          // TODO: also implementing scroll feature
          // Scrolling ideas: define top and bottom y coordinate for where scrolling should start
          // need to proportion based on screen size
      }, 1000);
    }
  }

  function checkStatus(response) {
    if (response.ok) {
      return response;
    } else {
       throw Error("Error in request: " + response.statusText);
    }
  }

  function $(id) {
    return document.getElementById(id);
  }

})();