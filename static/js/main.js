console.log("StorySpring is running!");

/* =========================================
   STORYSPRING TEXT TO SPEECH
========================================= */

document.addEventListener("DOMContentLoaded", function () {

    // Check if this page has the StorySpring TTS player
    const playButton = document.getElementById("playSpeech");

    if (!playButton) {
        return;
    }

    // Check browser support
    if (!("speechSynthesis" in window)) {

        const unsupported =
            document.getElementById("speechUnsupported");

        if (unsupported) {
            unsupported.style.display = "block";
        }

        document.getElementById("playSpeech").disabled = true;
        document.getElementById("pauseSpeech").disabled = true;
        document.getElementById("stopSpeech").disabled = true;

        return;
    }


    // -----------------------------------------
    // Elements
    // -----------------------------------------

    const pauseButton =
        document.getElementById("pauseSpeech");

    const stopButton =
        document.getElementById("stopSpeech");

    const speechStatus =
        document.getElementById("speechStatus");

    const speechRate =
        document.getElementById("speechRate");

    const speechVoice =
        document.getElementById("speechVoice");

    const storyContent =
        document.getElementById("storyContent");


    // Browser speech engine
    const speech = window.speechSynthesis;

    let voices = [];

    let utterance = null;


    // -----------------------------------------
    // Get Story Text
    // -----------------------------------------

    function getStoryText() {

        const clone =
            storyContent.cloneNode(true);

        // Remove decorative emoji
        const decoration =
            clone.querySelector(
                ".story-content-decoration"
            );

        if (decoration) {
            decoration.remove();
        }

        return clone.innerText.trim();
    }


    // -----------------------------------------
    // Load Voices
    // -----------------------------------------

    function loadVoices() {

        voices = speech.getVoices();

        speechVoice.innerHTML = "";

        const defaultOption =
            document.createElement("option");

        defaultOption.value = "";

        defaultOption.textContent =
            "Default Voice";

        speechVoice.appendChild(defaultOption);


        voices.forEach(function (voice, index) {

            const option =
                document.createElement("option");

            option.value = index;

            option.textContent =
                voice.name + " (" + voice.lang + ")";

            speechVoice.appendChild(option);

        });

    }


    loadVoices();


    // Some browsers load voices after page load
    speech.onvoiceschanged = function () {

        loadVoices();

    };


    // -----------------------------------------
    // PLAY / RESUME
    // -----------------------------------------

    playButton.addEventListener(
        "click",
        function () {

            // If currently paused, resume
            if (speech.paused) {

                speech.resume();

                speechStatus.textContent =
                    "🔊 Reading the story...";

                playButton.innerHTML =
                    '<i class="bi bi-volume-up-fill"></i> Reading';

                return;
            }


            const storyText =
                getStoryText();


            if (!storyText) {

                speechStatus.textContent =
                    "There is no story text to read.";

                return;
            }


            // Stop any previous speech
            speech.cancel();


            // Create speech
            utterance =
                new SpeechSynthesisUtterance(
                    storyText
                );


            // Reading speed
            utterance.rate =
                parseFloat(
                    speechRate.value
                );


            // Natural sounding pitch
            utterance.pitch = 1;


            // Selected voice
            if (speechVoice.value !== "") {

                const selectedVoice =
                    voices[
                        parseInt(
                            speechVoice.value
                        )
                    ];

                if (selectedVoice) {

                    utterance.voice =
                        selectedVoice;

                }
            }


            // ---------------------------------
            // Speech Started
            // ---------------------------------

            utterance.onstart =
                function () {

                    speechStatus.textContent =
                        "🔊 Reading the story...";

                    playButton.innerHTML =
                        '<i class="bi bi-volume-up-fill"></i> Reading';

                };


            // ---------------------------------
            // Speech Finished
            // ---------------------------------

            utterance.onend =
                function () {

                    speechStatus.textContent =
                        "Story finished!";

                    playButton.innerHTML =
                        '<i class="bi bi-play-fill"></i> Listen';

                };


            // ---------------------------------
            // Speech Cancelled
            // ---------------------------------

            utterance.oncancel =
                function () {

                    speechStatus.textContent =
                        "Story stopped.";

                    playButton.innerHTML =
                        '<i class="bi bi-play-fill"></i> Listen';

                };


            // ---------------------------------
            // Speech Error
            // ---------------------------------

            utterance.onerror =
                function () {

                    speechStatus.textContent =
                        "Something went wrong while reading the story.";

                    playButton.innerHTML =
                        '<i class="bi bi-play-fill"></i> Listen';

                };


            // Start speaking
            speech.speak(utterance);

        }
    );


    // -----------------------------------------
    // PAUSE
    // -----------------------------------------

    pauseButton.addEventListener(
        "click",
        function () {

            if (
                speech.speaking &&
                !speech.paused
            ) {

                speech.pause();

                speechStatus.textContent =
                    "⏸️ Story paused.";

            }

        }
    );


    // -----------------------------------------
    // STOP
    // -----------------------------------------

    stopButton.addEventListener(
        "click",
        function () {

            speech.cancel();

            speechStatus.textContent =
                "Story stopped.";

            playButton.innerHTML =
                '<i class="bi bi-play-fill"></i> Listen';

        }
    );


    // -----------------------------------------
    // CHANGE SPEED
    // -----------------------------------------

    speechRate.addEventListener(
        "change",
        function () {

            if (speech.speaking) {

                speech.cancel();

                speechStatus.textContent =
                    "Speed changed. Press Listen to continue.";

                playButton.innerHTML =
                    '<i class="bi bi-play-fill"></i> Listen';

            }

        }
    );


    // -----------------------------------------
    // CHANGE VOICE
    // -----------------------------------------

    speechVoice.addEventListener(
        "change",
        function () {

            if (speech.speaking) {

                speech.cancel();

                speechStatus.textContent =
                    "Voice changed. Press Listen to continue.";

                playButton.innerHTML =
                    '<i class="bi bi-play-fill"></i> Listen';

            }

        }
    );


    // -----------------------------------------
    // Stop when leaving page
    // -----------------------------------------

    window.addEventListener(
        "beforeunload",
        function () {

            speech.cancel();

        }
    );

});