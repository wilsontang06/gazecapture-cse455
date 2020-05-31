"use strict";
(function() {

  const WIDTH = 500;
  const HEIGHT = 375;

  let imageCapture;

  window.addEventListener("load", init);

  function init() {
    turnCamOn();
    $("captureButton").addEventListener("click", processImage);
    $("camButton").addEventListener("click", toggleCamera);
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

  function processImage() {
    // can put this in a loop or timer to constantly send capture images
    // while (the classlist contains capture is on)
    // for now, hopefully get one photo working

    imageCapture.takePhoto()
      .then(blob => {
        //let url = window.URL.createObjectURL(blob);
        // replace with sending the image
        // insert fetch call to backend
        //    for scrolling, use this button as a "start recording"
        //    so it can toggle the calls to the backend

        let canvas = document.createElement('canvas');
        canvas.width  = WIDTH;
        canvas.height = HEIGHT;
        let ctx = canvas.getContext("2d");
        let img = document.getElementById("webcam");
        ctx.drawImage(img, 0, 0, WIDTH, HEIGHT);

        let jpegFile = canvas.toDataURL("image/jpeg");

        let params = new FormData();
        params.append("image", jpegFile);

        fetch("http://127.0.0.1:5000/model", {method: "POST", body: params})
          .then(checkStatus)
          .then(resp => resp.text())
          .then(processCoordinates)
          .catch(console.log);
      })
  }

  function processCoordinates(response) {
    $("dummy").src = response;
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