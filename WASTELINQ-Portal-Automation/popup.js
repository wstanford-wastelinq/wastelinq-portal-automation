const PROFILE_URL = "https://hzz3uvi5jgjnsomqchehpupqim0iizju.lambda-url.us-east-2.on.aws/";
const MAPPING_URL = "https://gf6fbx4vhdd5lcq4qmfmvexazi0qgiwp.lambda-url.us-east-2.on.aws/";
let profileData = null;
let mappedData = null;

// Function to ensure content script is injected
async function ensureContentScriptInjected(tabId) {
    try {
        await chrome.scripting.executeScript({
            target: { tabId },
            files: ['content.js']
        });
    } catch (error) {
        // If script is already injected, this will error, which is fine
        console.log('Content script may already be injected');
    }
}

document.getElementById('searchButton').addEventListener('click', async () => {
    const profileId = document.getElementById('profileId').value;
    if (!profileId) {
        showError("Please enter a Profile ID");
        return;
    }

    showStatus("Searching...", "loading");
    document.getElementById('result').style.display = 'none';

    try {
        // Fetch profile data
        const profileResponse = await fetch(`${PROFILE_URL}?id=${profileId}`);
        if (!profileResponse.ok) {
            throw new Error(`HTTP error! status: ${profileResponse.status}`);
        }

        profileData = await profileResponse.json();
        
        // Display the results
        document.getElementById('displayId').textContent = profileData.CustomerProfile_id || profileId;
        document.getElementById('displayName').textContent = profileData.Name || profileName;
        document.getElementById('wasteStream').textContent = profileData.WasteStreamDescription || 'N/A';
        document.getElementById('process').textContent = profileData.ProcessGeneratingTheWaste || 'N/A';
        document.getElementById('result').style.display = 'block';
        document.getElementById('status').style.display = 'none';

    } catch (error) {
        showError(`Error fetching profile: ${error.message}`);
    }
});

document.getElementById('fillButton').addEventListener('click', async () => {
    if (!profileData) {
        showError("No profile data available");
        return;
    }

    const requestData = {
        targetPortal: "tradebe",
        ...profileData  
    };

    try {
        showStatus("Mapping data...", "loading");

        const mappingResponse = await fetch(MAPPING_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });

        if (!mappingResponse.ok) {
            throw new Error(`Mapping error! status: ${mappingResponse.status}`);
        }

        mappedData = await mappingResponse.json();

        showStatus("Preparing to fill form...", "loading");

        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

        // Ensure content script is injected
        await ensureContentScriptInjected(tab.id);

        // Wait longer for the script to initialize
        await new Promise(resolve => setTimeout(resolve, 1000));

        showStatus("Filling form...", "loading");

        try {
            const response = await new Promise((resolve, reject) => {
                const timeoutId = setTimeout(() => {
                    reject(new Error("Form fill timed out"));
                }, 240000); // Increased timeout to 60 seconds

                chrome.tabs.sendMessage(tab.id, {
                    action: "fillForm",
                    data: mappedData
                }, response => {
                    clearTimeout(timeoutId);
                    if (chrome.runtime.lastError) {
                        reject(new Error(chrome.runtime.lastError.message));
                    } else {
                        resolve(response);
                    }
                });
            });

            if (response.status === "success") {
                showStatus("Form filled successfully!", "success");
            } else if (response.status === "partial") {
                showStatus(`Partially filled. Failed fields: ${response.failedFields.join(", ")}`, "warning");
            } else {
                showError(`Error filling form: ${response.error}`);
            }
        } catch (error) {
            throw new Error(`Form filling error: ${error.message}`);
        }

    } catch (error) {
        showError(`Error processing data: ${error.message}`);
    }
});

function showError(message) {
    const status = document.getElementById('status');
    status.className = 'error';
    status.style.display = 'block';
    status.textContent = message;
}

function showStatus(message, type) {
    const status = document.getElementById('status');
    status.className = type;
    status.style.display = 'block';
    status.textContent = message;
}