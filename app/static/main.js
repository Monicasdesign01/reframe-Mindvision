const form = document.getElementById("worry-form");
const textInput = document.getElementById("text-input");
const audioInput = document.getElementById("audio-input");
const loadingSection = document.getElementById("loading-section");
const resultSection = document.getElementById("result-section");
const crisisSection = document.getElementById("crisis-section");

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  resultSection.classList.add("hidden");
  crisisSection.classList.add("hidden");
  loadingSection.classList.remove("hidden");

  const formData = new FormData();
  formData.append("text", textInput.value);
  if (audioInput.files[0]) {
    formData.append("audio", audioInput.files[0]);
  }

  try {
    const res = await fetch("/process", { method: "POST", body: formData });
    const data = await res.json();
    loadingSection.classList.add("hidden");

    if (data.error) {
      alert(data.error);
      return;
    }

    if (data.crisis) {
      crisisSection.classList.remove("hidden");
      crisisSection.querySelector(".crisis-box").textContent = data.message;
      return;
    }

    document.getElementById("summary").textContent = data.summary;
    document.getElementById("narrative").textContent = data.narrative;
    document.getElementById("citation").textContent = `Technique: ${data.technique.name} — ${data.technique.citation}`;
    resultSection.classList.remove("hidden");

    const audioPlayer = document.getElementById("audio-player");
    if (data.audio_url) {
      audioPlayer.src = data.audio_url;
      audioPlayer.classList.remove("hidden");
    }

    pollImage(data.image_status_url);
  } catch (err) {
    loadingSection.classList.add("hidden");
    alert("Something went wrong: " + err.message);
  }
});

function pollImage(statusUrl) {
  const img = document.getElementById("result-image");
  const loadingText = document.getElementById("image-loading");
  const interval = setInterval(async () => {
    const res = await fetch(statusUrl);
    const data = await res.json();
    if (data.status === "done") {
      clearInterval(interval);
      img.src = data.image_url;
      img.classList.remove("hidden");
      loadingText.classList.add("hidden");
    } else if (data.status === "error") {
      clearInterval(interval);
      loadingText.textContent = "Image generation failed, but your text and audio are ready above.";
    }
  }, 2000);
}
