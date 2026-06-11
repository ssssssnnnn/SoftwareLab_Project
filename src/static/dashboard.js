// State Management
let cachedData = null;
let currentFastestConfig = { url: "", type: "" };
let isFetching = false;

// Helper Utility: Formatting dynamic code snippets based on ecosystem type
function generateConfigSnippet(url, type) {
  if (type === "PyPI") return `pip config set global.index-url ${url}`;
  if (type === "NPM") return `npm config set registry ${url}`;
  return `# No directive mapping variant found for: ${url}`;
}

// Helper Utility: Native OS Clipboard interface handler
async function copySnippetToClipboard(textSnippet) {
  try {
    await window.navigator.clipboard.writeText(textSnippet);
    window.alert(
      `Configuration command copied explicitly to clipboard:\n\n${textSnippet}`,
    );
  } catch {
    window.alert("Clipboard access blocked by browser environment permissions.");
  }
}

function copyFastestSnippet() {
  if (currentFastestConfig.url) {
    const command = generateConfigSnippet(
      currentFastestConfig.url,
      currentFastestConfig.type,
    );
    copySnippetToClipboard(command);
  }
}

// Dynamically populates the dropdown options based on the unique repository types returned by the server
function populateFilterDropdown(mirrors) {
  const filterSelect = document.getElementById("repo-filter");
  if (!filterSelect) return;

  const currentSelection = filterSelect.value;
  const uniqueTypes = [...new Set(mirrors.map((m) => m.type))].filter(Boolean);

  // Keep the default option
  filterSelect.innerHTML = '<option value="ALL">All Types</option>';

  uniqueTypes.forEach((type) => {
    const option = document.createElement("option");
    option.value = type;
    option.textContent = type;
    filterSelect.appendChild(option);
  });

  // Restore selection state if it still exists in the new options list
  if (uniqueTypes.includes(currentSelection)) {
    filterSelect.value = currentSelection;
  } else {
    filterSelect.value = "ALL";
  }
}

// Process data locally to filter items and accurately recalculate the optimal route
function processAndRenderData() {
  if (!cachedData || !cachedData.mirrors) return;

  const selectedFilter = document.getElementById("repo-filter")?.value || "ALL";
  const tableBody = document.getElementById("metrics-table-body");

  // 1. Filter mirrors array locally
  const filteredMirrors =
    selectedFilter === "ALL"
      ? cachedData.mirrors
      : cachedData.mirrors.filter((mirror) => mirror.type === selectedFilter);

  // 2. Recalculate metrics dynamically based ONLY on the current filter view
  const totalCount = filteredMirrors.length;
  const onlineMirrors = filteredMirrors.filter((m) => m.status === "Online");
  const onlineCount = onlineMirrors.length;

  // Find the actual fastest mirror from the filtered online subset
  let fastestMirror = null;
  if (onlineCount > 0) {
    fastestMirror = onlineMirrors.reduce((prev, curr) => {
      return prev.latency_ms < curr.latency_ms ? prev : curr;
    });
  }

  // Calculate dynamic average latency for visible nodes
  let avgLatency = 0;
  if (onlineCount > 0) {
    const totalLatency = onlineMirrors.reduce(
      (sum, m) => sum + (m.latency_ms || 0),
      0,
    );
    avgLatency = (totalLatency / onlineCount).toFixed(1);
  }

  // 3. Update summary card UI elements
  document.getElementById("metric-count").innerText =
    `${totalCount} / ${onlineCount}`;
  document.getElementById("metric-fastest").innerText = fastestMirror
    ? fastestMirror.name
    : "N/A";
  document.getElementById("metric-latency").innerHTML =
    `${avgLatency} <span class="text-lg font-normal text-gray-500">ms</span>`;

  // Manage top level setup configuration button context
  if (fastestMirror) {
    currentFastestConfig.url = fastestMirror.url;
    currentFastestConfig.type = fastestMirror.type;
    document.getElementById("btn-copy-fastest").classList.remove("hidden");
  } else {
    currentFastestConfig = { url: "", type: "" };
    document.getElementById("btn-copy-fastest").classList.add("hidden");
  }

  // 4. Render Table Layout Rows
  tableBody.innerHTML = "";
  if (filteredMirrors.length === 0) {
    tableBody.innerHTML = `<tr><td colspan="6" class="text-center py-10 text-gray-500">No endpoints found matching this repository filter.</td></tr>`;
    return;
  }

  filteredMirrors.forEach((mirror) => {
    const rowHtml = `
            <tr class="hover:bg-gray-700/30 transition-colors">
                <td class="px-6 py-4">
                    <div class="font-semibold text-gray-100">${mirror.name}</div>
                    <div class="text-xs text-gray-500 font-mono mt-0.5 truncate max-w-xs">${mirror.url}</div>
                </td>
                <td class="px-6 py-4">
                    <span class="px-2 py-1 text-xs font-bold uppercase rounded bg-gray-900 border border-gray-700 text-gray-300">
                        ${mirror.type}
                    </span>
                </td>
                <td class="px-6 py-4 text-center">
                    <span class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      mirror.status === "Online"
                        ? "bg-green-500/10 text-green-400"
                        : "bg-red-500/10 text-red-400"
                    }">
                        <span class="w-1.5 h-1.5 rounded-full ${mirror.status === "Online" ? "bg-green-400" : "bg-red-400"}"></span>
                        ${mirror.status}
                    </span>
                </td>
                <td class="px-6 py-4 text-right font-mono text-gray-300">
                    ${mirror.status === "Online" ? `${mirror.latency_ms} ms` : "--"}
                </td>
                <td class="px-6 py-4 text-right font-mono text-teal-400 font-semibold">
                    ${mirror.status === "Online" ? `${mirror.speed_mbs} MB/s` : "--"}
                </td>
                <td class="px-6 py-4 text-center">
                    ${
                      mirror.status === "Online"
                        ? `
                        <button data-url="${mirror.url}" data-type="${mirror.type}" class="btn-copy-row text-xs bg-teal-600/20 hover:bg-teal-600 text-teal-400 hover:text-white px-3 py-1 rounded border border-teal-500/30 transition-all font-medium">
                            Copy Setup Snippet
                        </button>
                    `
                        : `
                        <span class="text-xs text-gray-600 italic">Offline</span>
                    `
                    }
                </td>
            </tr>
        `;
    tableBody.insertAdjacentHTML("beforeend", rowHtml);
  });
}

// Main API Connector and UI Data Retriever
async function fetchMetrics(forceRefresh = false) {
  if (isFetching) return;
  isFetching = true;

  const btnIcon = document.getElementById("refresh-icon");
  const btnText = document.getElementById("refresh-text");
  const tableBody = document.getElementById("metrics-table-body");

  if (btnIcon && btnText) {
    btnIcon.classList.add("animate-spin");
    btnText.innerText = forceRefresh ? "Benchmarking..." : "Loading...";
  }

  tableBody.innerHTML = `
        <tr>
            <td colspan="6" class="text-center py-10 text-gray-400">
                <div class="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-teal-500 mr-2 align-middle"></div>
                Testing live mirror network targets now... (Takes ~5-10 seconds)
            </td>
        </tr>
    `;

  try {
    const targetUrl = forceRefresh
      ? "/api/forcerun"
      : `/api/metrics?nocache=${Date.now()}`;
    const fetchOptions = forceRefresh ? { method: "POST" } : { method: "GET" };

    const response = await fetch(targetUrl, fetchOptions);
    if (!response.ok) throw new Error("API pipeline error.");

    // Save payload globally into cache state
    cachedData = await response.json();

    // Setup dropdown options based on returned list values
    populateFilterDropdown(cachedData.mirrors);

    // Process UI metrics calculation
    processAndRenderData();
  } catch (error) {
    console.error("Dashboard render runtime issue:", error);
    tableBody.innerHTML = `<tr><td colspan="6" class="text-center py-10 text-red-400">Error connecting to diagnostics pipeline interface.</td></tr>`;
  } finally {
    if (btnIcon && btnText) {
      btnIcon.classList.remove("animate-spin");
      btnText.innerText = "Refresh Diagnostics";
    }
    isFetching = false;
  }
}

// Setup a polling logic listening for data updates from backend
function startPollingForUpdates() {
  // Poll every 5 seconds
  const intervalId = window.setInterval(async () => {
    try {
      const response = await fetch(`/api/metrics?nocache=${Date.now()}`);
      if (response.ok) {
        const freshData = await response.json();

        if (JSON.stringify(freshData) !== JSON.stringify(cachedData)) {
          cachedData = freshData;
          populateFilterDropdown(cachedData.mirrors);
          processAndRenderData();
          console.log(
            "Dashboard state auto-synchronized with background scheduler.",
          );
        }
      }
    } catch (err) {
      console.error("Polling sync error:", err);
    }
  }, 5000);

  // Cleanup the interval
  window.addEventListener("beforeunload", () => window.clearInterval(intervalId));
}

// Central Event Binding Layer after DOM finishes parsing
window.addEventListener("DOMContentLoaded", () => {
  fetchMetrics(false);
  startPollingForUpdates();

  document.getElementById("refresh-btn")?.addEventListener("click", () => {
    fetchMetrics(true);
  });

  document
    .getElementById("btn-copy-fastest")
    ?.addEventListener("click", copyFastestSnippet);

  document
    .getElementById("repo-filter")
    ?.addEventListener("change", processAndRenderData);

  document
    .getElementById("metrics-table-body")
    ?.addEventListener("click", (event) => {
      const rowButton = event.target.closest(".btn-copy-row");
      if (rowButton) {
        const url = rowButton.getAttribute("data-url");
        const type = rowButton.getAttribute("data-type");
        const snippet = generateConfigSnippet(url, type);
        copySnippetToClipboard(snippet);
      }
    });
});
