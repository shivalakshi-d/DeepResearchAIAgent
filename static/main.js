"use strict";

// =========================================
// DOM ELEMENTS
// =========================================

const topicInput = document.getElementById("topicInput");
const researchBtn = document.getElementById("researchBtn");

const progressSection = document.getElementById("progressSection");
const progressTitle = document.getElementById("progressTitle");

const errorMessage = document.getElementById("errorMessage");
const errorText = document.getElementById("errorText");

const resultsSection = document.getElementById("resultsSection");
const resultsTopic = document.getElementById("resultsTopic");
const reportContent = document.getElementById("reportContent");

const sourcesCount = document.getElementById("sourcesCount");
const modelBadge = document.getElementById("modelBadge");
const tokensBadge = document.getElementById("tokensBadge");

const sourcesList = document.getElementById("sourcesList");
const sourcesPanel = document.getElementById("sourcesPanel");

const copyBtn = document.getElementById("copyBtn");

const imageInput = document.getElementById("imageInput");
const imagePreview = document.getElementById("imagePreview");
const imagePreviewContainer = document.getElementById(
    "imagePreviewContainer"
);
const removeImageBtn = document.getElementById("removeImageBtn");

const analyzedImage = document.getElementById("analyzedImage");
const analyzedImageContainer = document.getElementById(
    "analyzedImageContainer"
);
const analysisLayout = document.getElementById("analysisLayout");

const historyList = document.getElementById("history-list");

let selectedImage = null;
let selectedImageDataUrl = "";
let rawMarkdown = "";
let isResearching = false;


// =========================================
// HELPER FUNCTIONS
// =========================================

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, character => {
        const replacements = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;"
        };

        return replacements[character];
    });
}

function fillTopic(topic) {
    topicInput.value = topic;
    topicInput.focus();
}

function shake(element) {
    element.classList.remove("shake");
    void element.offsetWidth;
    element.classList.add("shake");

    setTimeout(() => {
        element.classList.remove("shake");
    }, 400);
}

function showError(message) {
    errorText.textContent = message;
    errorMessage.hidden = false;
}

function hideError() {
    errorMessage.hidden = true;
    errorText.textContent = "";
}


// =========================================
// PROGRESS DISPLAY
// =========================================

function updateProgress(message, activeStep = 1) {
    progressTitle.textContent = message;

    for (let i = 1; i <= 3; i++) {
        const step = document.getElementById(`step${i}`);

        if (!step) {
            continue;
        }

        step.classList.remove("active", "done");

        if (i < activeStep) {
            step.classList.add("done");
        } else if (i === activeStep) {
            step.classList.add("active");
        }
    }
}

function completeProgress() {
    for (let i = 1; i <= 3; i++) {
        const step = document.getElementById(`step${i}`);

        if (step) {
            step.classList.remove("active");
            step.classList.add("done");
        }
    }
}


// =========================================
// START RESEARCH
// =========================================

async function startResearch() {
    if (isResearching) {
        return;
    }

    const topic = topicInput.value.trim();

    if (!topic && !selectedImage) {
        showError("Please enter a research topic or upload an image.");
        shake(topicInput);
        topicInput.focus();
        return;
    }

    hideError();

    resultsSection.hidden = true;
    progressSection.hidden = false;

    isResearching = true;
    researchBtn.disabled = true;

    const originalButtonText = researchBtn.innerHTML;
    researchBtn.innerHTML = '<span class="btn-text">Working...</span>';

    const imageBeingAnalyzed = selectedImage;
    const imageDataForResult = selectedImageDataUrl;

    const isImageResearch = Boolean(imageBeingAnalyzed);

    updateProgress(
        isImageResearch
            ? "Analyzing your image..."
            : "Searching the web...",
        1
    );

    const progressTimer = setTimeout(() => {
        if (isResearching) {
            updateProgress(
                isImageResearch
                    ? "AI is examining the image..."
                    : "Reading and analyzing sources...",
                2
            );
        }
    }, 2500);

    const secondProgressTimer = setTimeout(() => {
        if (isResearching) {
            updateProgress("Generating your answer...", 3);
        }
    }, 6500);

    try {
        let response;

        // Image request uses multipart/form-data.
        if (imageBeingAnalyzed) {
            const formData = new FormData();

            formData.append(
                "query",
                topic || "Describe this image in detail."
            );

            formData.append("image", imageBeingAnalyzed);

            response = await fetch("/research", {
                method: "POST",
                body: formData
            });

        } else {
            // Text research uses JSON.
            response = await fetch("/research", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    query: topic
                })
            });
        }

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(
                data.error || "Research failed. Please try again."
            );
        }

        completeProgress();

        // Display the report and the analyzed image.
        renderResults(data, imageDataForResult);

        // Refresh recent searches.
        await loadHistory();

        // Clear the upload selection only after successful analysis.
        // The analyzed image remains visible in the results section.
        if (imageBeingAnalyzed) {
            selectedImage = null;
            selectedImageDataUrl = "";
            imageInput.value = "";
            imagePreview.src = "";
            imagePreviewContainer.hidden = true;
        }

    } catch (error) {
        console.error("Research error:", error);

        showError(
            error.message ||
            "Unable to connect to the research server. Make sure Flask is running."
        );

    } finally {
        clearTimeout(progressTimer);
        clearTimeout(secondProgressTimer);

        progressSection.hidden = true;
        researchBtn.disabled = false;
        researchBtn.innerHTML = originalButtonText;

        isResearching = false;
    }
}


// =========================================
// RENDER RESULTS
// =========================================

function renderResults(data, imageDataUrl = "") {
    rawMarkdown = data.report || data.answer || "No report generated.";

    resultsTopic.textContent = data.topic || "Research Results";

    // Render Markdown if the library is available.
    if (window.marked && typeof window.marked.parse === "function") {
        reportContent.innerHTML = window.marked.parse(rawMarkdown);
    } else {
        reportContent.textContent = rawMarkdown;
    }

    // Metadata.
    const sourceNumber = Number(data.sources_analyzed ?? 0);

    sourcesCount.textContent =
        `${sourceNumber} source${sourceNumber === 1 ? "" : "s"}`;

    modelBadge.textContent =
        `Model: ${data.model_used || "AI"}`;

    tokensBadge.textContent =
        `Tokens: ${Number(data.tokens_used ?? 0)}`;

    // Image display.
    const hasImage = Boolean(imageDataUrl);

    if (hasImage) {
        analyzedImage.src = imageDataUrl;
        analyzedImageContainer.hidden = false;
        analysisLayout.classList.add("has-image");
    } else {
        analyzedImage.removeAttribute("src");
        analyzedImageContainer.hidden = true;
        analysisLayout.classList.remove("has-image");
    }

    // Sources.
    sourcesList.replaceChildren();

    const sources = Array.isArray(data.sources)
        ? data.sources
        : [];

    if (sources.length > 0) {
        sourcesPanel.hidden = false;

        sources.forEach((source, index) => {
            const row = document.createElement("div");
            row.className = "source-item";

            const number = document.createElement("span");
            number.className = "source-number";
            number.textContent = String(index + 1).padStart(2, "0");

            const link = document.createElement("a");
            link.className = "source-link";

            const title = source.title || source.url || "Source";
            link.textContent = title;

            try {
                const parsedUrl = new URL(source.url);

                if (
                    parsedUrl.protocol === "https:" ||
                    parsedUrl.protocol === "http:"
                ) {
                    link.href = parsedUrl.href;
                    link.target = "_blank";
                    link.rel = "noopener noreferrer";
                } else {
                    link.removeAttribute("href");
                }
            } catch {
                link.removeAttribute("href");
            }

            row.append(number, link);
            sourcesList.appendChild(row);
        });

    } else {
        sourcesPanel.hidden = true;
    }

    resultsSection.hidden = false;

    resultsSection.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });
}


// =========================================
// COPY REPORT
// =========================================

async function copyReport() {
    try {
        await navigator.clipboard.writeText(rawMarkdown);

        copyBtn.textContent = "Copied!";
        copyBtn.classList.add("copied");

        setTimeout(() => {
            copyBtn.textContent = "Copy Report";
            copyBtn.classList.remove("copied");
        }, 1800);

    } catch (error) {
        console.error("Copy failed:", error);

        showError(
            "Could not copy the report. Please select and copy the text manually."
        );
    }
}


// =========================================
// RESET
// =========================================

function resetAndFocus() {
    resultsSection.hidden = true;
    hideError();

    topicInput.value = "";
    topicInput.focus();

    selectedImage = null;
    selectedImageDataUrl = "";

    imageInput.value = "";
    imagePreview.src = "";
    imagePreviewContainer.hidden = true;

    analyzedImage.removeAttribute("src");
    analyzedImageContainer.hidden = true;
    analysisLayout.classList.remove("has-image");

    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });
}


// =========================================
// IMAGE UPLOAD
// =========================================

imageInput.addEventListener("change", event => {
    const file = event.target.files?.[0];

    if (!file) {
        return;
    }

    const allowedTypes = [
        "image/jpeg",
        "image/png",
        "image/webp"
    ];

    if (!allowedTypes.includes(file.type)) {
        showError("Please select a JPG, PNG, or WEBP image.");
        imageInput.value = "";
        return;
    }

    const maxSize = 10 * 1024 * 1024;

    if (file.size > maxSize) {
        showError("The image must be smaller than 10 MB.");
        imageInput.value = "";
        return;
    }

    hideError();

    selectedImage = file;

    const reader = new FileReader();

    reader.onload = () => {
        selectedImageDataUrl = String(reader.result || "");

        imagePreview.src = selectedImageDataUrl;
        imagePreviewContainer.hidden = false;
    };

    reader.onerror = () => {
        showError("Could not read the selected image.");
        selectedImage = null;
        selectedImageDataUrl = "";
        imageInput.value = "";
        imagePreviewContainer.hidden = true;
    };

    reader.readAsDataURL(file);
});

removeImageBtn.addEventListener("click", () => {
    selectedImage = null;
    selectedImageDataUrl = "";

    imageInput.value = "";
    imagePreview.src = "";
    imagePreviewContainer.hidden = true;
});


// =========================================
// SEARCH HISTORY
// =========================================

async function loadHistory() {
    try {
        const response = await fetch("/history");

        if (!response.ok) {
            throw new Error("Could not load search history.");
        }

        const history = await response.json();

        renderHistory(history);

    } catch (error) {
        console.error("History loading error:", error);

        historyList.innerHTML =
            '<p class="history-empty">Unable to load recent searches.</p>';
    }
}

function renderHistory(history) {
    historyList.replaceChildren();

    if (!Array.isArray(history) || history.length === 0) {
        const emptyMessage = document.createElement("p");
        emptyMessage.className = "history-empty";
        emptyMessage.textContent = "No searches yet.";

        historyList.appendChild(emptyMessage);
        return;
    }

    history.forEach((item, index) => {
        const row = document.createElement("div");
        row.className = "history-item";

        const queryButton = document.createElement("button");
        queryButton.type = "button";
        queryButton.className = "history-query";
        queryButton.textContent = item.query || "Untitled search";
        queryButton.title = item.query || "Open previous report";

        queryButton.addEventListener("click", () => {
            openHistoryItem(item);
        });

        const deleteButton = document.createElement("button");
        deleteButton.type = "button";
        deleteButton.className = "history-delete";
        deleteButton.textContent = "×";
        deleteButton.title = "Delete search";
        deleteButton.setAttribute("aria-label", "Delete search");

        deleteButton.addEventListener("click", async () => {
            await deleteHistoryItem(index);
        });

        row.append(queryButton, deleteButton);
        historyList.appendChild(row);
    });
}

function openHistoryItem(item) {
    hideError();

    topicInput.value = item.query || "";

    // Previous reports are stored as text.
    // The original uploaded image bytes are not stored by app.py.
    renderResults({
        success: true,
        topic: item.query || "Previous Research",
        report: item.report || "No saved report available.",
        sources: Array.isArray(item.sources) ? item.sources : [],
        sources_analyzed: Array.isArray(item.sources)
            ? item.sources.length
            : 0,
        model_used: "Saved report",
        tokens_used: 0
    });

    // Image history cannot restore the original image unless its data
    // was stored separately. Do not show a different, previously selected image.
    analyzedImage.removeAttribute("src");
    analyzedImageContainer.hidden = true;
    analysisLayout.classList.remove("has-image");
}

async function deleteHistoryItem(index) {
    try {
        const response = await fetch(`/history/${index}`, {
            method: "DELETE"
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(data.error || "Could not delete this search.");
        }

        await loadHistory();

    } catch (error) {
        console.error("History deletion error:", error);
        showError(error.message || "Could not delete this search.");
    }
}


// =========================================
// KEYBOARD SUPPORT
// =========================================

topicInput.addEventListener("keydown", event => {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        startResearch();
    }
});


// =========================================
// INITIALIZE
// =========================================

document.addEventListener("DOMContentLoaded", () => {
    loadHistory();
});

