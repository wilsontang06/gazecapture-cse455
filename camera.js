"use strict";
(function() {

  const WIDTH = 500;
  const HEIGHT = 375;
  const HOST = "http://gazecapture455.westus2.cloudapp.azure.com:5000/model"
  const PX_IN_CM = 37.795275591;

  let timer;
  let isSendingLive = false;

  window.addEventListener("load", init);

  function init() {
    let canvas = document.createElement('canvas');
    canvas.width  = WIDTH;
    canvas.height = HEIGHT;
    let ctx = canvas.getContext("2d");

    turnCamOn();
    $("camButton").addEventListener("click", toggleCamera);
    $("captureButton").addEventListener("click", function() {
      processImage(canvas, ctx, false);
    });
    $("scrollButton").addEventListener("click", function() {
      processStreamOfImages(canvas, ctx);
    });
  }

  function toggleCamera() {
    if ($("camButton").classList.contains("camButtonOn")) {
      // Turn camera on
      turnCamOn();
      $("captureButton").disabled = false;
      $("camButton").innerText = "Turn Webcam Off";
      $("scrollButton").disabled = false;
    } else {
      // Turn camera off
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

  function processImage(canvas, ctx, scroll) {
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
      .then(resp => processCoordinates(resp, scroll))
      .catch(errorResponse);
  }

  function processCoordinates(response, scroll) {
    isSendingLive = false;
    let coords = response.split(" ");

    // keep coordinates in bounds of window
    let x = Math.max(50, Math.min(window.innerWidth - 75, coords[0] * PX_IN_CM * 1.5));
    let y = Math.max(50, Math.min(window.innerHeight - 75, coords[1] * PX_IN_CM * 2.5));
    console.log("x:" + x + " y:" + y);

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

    // Scroll using these coordinates
    if (scroll) {
      scrollFromY(y);
    }
  }

  /*
    Scrolls the page based on a given y coordinate.
    Thresholds for scrolling are commented in the function body.
  */
  function scrollFromY(y) {
    // The proportion of the top and bottom of the page that are considered scroll areas
    // i.e. if the pct = 0.2, then the page will scroll when y is in the top 20% or bottom 20% of the page height
    const edgeHeightPct = 0.3;

    // How many px to scroll
    const scrollAmount = 200;

    // Scroll based on the region
    if(y <= window.innerHeight * edgeHeightPct) {
      // Top scroll region
      scrollBy(0, -scrollAmount);
    } else if(y >= window.innerHeight * (1 - edgeHeightPct)) {
      // Bottom scroll region
      scrollBy(0, scrollAmount);
    }
  }
  window.s = scrollFromY;

  function processStreamOfImages(canvas, ctx) {
    let scrollBtn = $("scrollButton");
    if (timer != null) {
      // if timer already set, disable and turn off scrolling
      clearInterval(timer);
      timer = null;
      isSendingLive = false;
      scrollBtn.innerText = "Click to Scroll";
    } else {
      // if no timer, enable scrolling and constantly send images to model in intervals
      scrollBtn.innerText = "Stop Scrolling";
      timer = setInterval(function() {
        if (!isSendingLive) {
          processImage(canvas, ctx, true);
          isSendingLive = true;
        }
      }, 1000);
    }
  }

  function errorResponse(err) {
    isSendingLive = false;
    console.log(err);
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
