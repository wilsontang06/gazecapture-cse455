"use strict";
(function() {

  let imageCapture;

  window.addEventListener("load", init);

  function init() {
    turnCamOn();
    $("captureButton").addEventListener("click", processImage);
    $("camButton").addEventListener("click", toggleCamera);
  }

  function processImage() {
    // can put this in a loop or timer to constantly send capture images
    // for now, hopefully get one photo working

    imageCapture.takePhoto()
      .then(blob => {
        let url = window.URL.createObjectURL(blob);
        alert(url); // replace with sending the image
        // insert fetch call to backend
        //    for scrolling, use this button as a "start recording"
        //    so it can toggle the calls to the backend

        window.URL.revokeObjectURL(url);
      })
  }

  function toggleCamera() {
    if ($("camButton").classList.contains("camButtonOn")) {
      turnCamOn();
      $("camButton").innerText = "Turn Webcam Off";
    } else {
      $("webcam").srcObject.getTracks()[0].stop();
      $("camButton").innerText = "Turn Webcam On";
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
          imageCapture = new ImageCapture(mediaStreamTrack);
          video.play();
        })
        .catch(function (e) {
          alert("Something went wrong!");
        });
    }
  }

  function $(id) {
    return document.getElementById(id);
  }

})();