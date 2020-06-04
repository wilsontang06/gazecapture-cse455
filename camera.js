"use strict";
(function() {

  const WIDTH = 500;
  const HEIGHT = 375;
  const HOST = "http://gazecapture455.westus2.cloudapp.azure.com:5000/model"
  const PX_IN_CM = 37.795275591;

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

  function pxToMm(px) {
    const cm = px / PX_IN_CM; // https://stackoverflow.com/questions/50829074/how-to-convert-pixels-to-cm-in-javascript#:~:text=It%20is%20used%20in%20most%20browsers.&text=If%20you%20just%20want%20to,conversion%20of%20px%20to%20cm.
    return cm * 10;
  }

  function processImage(canvas, ctx) {
    // capture the current image from the webcam
    let img = document.getElementById("webcam");
    ctx.drawImage(img, 0, 0, WIDTH, HEIGHT);
    let jpegFile = canvas.toDataURL("image/jpeg");

    let params = new FormData();
    params.append("image", jpegFile);
    params.append("screenWidthMm", pxToMm(window.innerWidth));
    params.append("screenHeightMm", pxToMm(window.innerHeight));

    // sends the image to the backend to be evaluated with the model
    fetch(HOST, {method: "POST", body: params})
      .then(checkStatus)
      .then(resp => resp.text())
      .then(processCoordinates)
      .catch(console.log);
  }

  function processCoordinates(response) {
    let coords = response.split(" ");

    // keep coordinates in bounds of window
    let x = max(50, min(window.innerWidth, coords[0] * PX_IN_CM));
    let y = max(50, min(widow.innerHeight, coords[1] * PX_IN_CM));
    console.log(x + " " + y);

    // create the dot to display on screen
    let circle = document.createElement("div");
    circle.id = "circle";
    circle.style.left = x + "px";
    circle.style.top = y + "px";

    // delete old circle
    let oldCircle = $("circle")
    if (oldCircle) {
      oldCircle.remove();
    }

    document.body.appendChild(circle);
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
