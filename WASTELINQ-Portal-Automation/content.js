console.log("Form Filler script loaded and waiting for commands");

async function simulateTabKey(element) {
    element.dispatchEvent(new KeyboardEvent('keydown', {
        key: 'Tab',
        code: 'Tab',
        keyCode: 9,
        which: 9,
        bubbles: true
    }));
}

async function simulateTyping(element, text) {
    element.value = '';
    element.dispatchEvent(new Event('input', { bubbles: true }));
    await new Promise(resolve => setTimeout(resolve, 300));
    
    element.value = text;
    element.dispatchEvent(new Event('input', { bubbles: true }));
    element.dispatchEvent(new Event('change', { bubbles: true }));
}

async function handleSAPMultiSelect(id, values) {
    console.log(`Handling SAP multi-select for ${id} with values:`, values);
    
    const input = findElementInPage(id);
    if (!input) {
        console.log(`Input field ${id} not found`);
        return false;
    }

    try {
        input.click();
        await new Promise(resolve => setTimeout(resolve, 500));

        for (const value of values) {
            await simulateTyping(input, value);
            
            await simulateTabKey(input);
            await new Promise(resolve => setTimeout(resolve, 500));

            input.value = '';
            input.dispatchEvent(new Event('input', { bubbles: true }));
            await new Promise(resolve => setTimeout(resolve, 1000));
        }

        return true;
    } catch (error) {
        console.log(`Error in handleSAPMultiSelect: ${error}`);
        return false;
    }
}



async function handleDropdownInput(id, value) {
    const input = await waitForElement(id);
    if (!input) return false;

    try {
        // Clear and type the value
        await simulateTyping(input, value);
        await new Promise(resolve => setTimeout(resolve, 250));

        // Wait for listbox to appear
        const listboxId = input.getAttribute('aria-controls');
        let listbox = null;
        
        // Try multiple ways to find the listbox
        for (let i = 0; i < 5; i++) {
            listbox = document.getElementById(listboxId) || 
                     document.querySelector('[role="listbox"]');
            if (listbox) break;
            await new Promise(resolve => setTimeout(resolve, 100));
        }

        if (listbox) {
            const firstItem = listbox.querySelector('[role="option"]');
            if (firstItem) {
                firstItem.click();
                return true;
            }
        }

        // If no listbox/item found, try tabbing
        await simulateTabKey(input);
        await new Promise(resolve => setTimeout(resolve, 300));

        return true;
    } catch (error) {
        console.log(`Error in handleDropdownInput: ${error}`);
        return false;
    }
}

async function setFieldValue(id, value) {
    console.log(`Setting field value for ${id}:`, value);

    const element = await waitForElement(id);
    if (!element) {
        console.log(`Element not found: ${id}`);
        return false;
    }

    try {
        // Handle SAP multi-select components
        if (Array.isArray(value) && id.includes('__box') && 
            (element.classList.contains('sapMInputBaseInner') || 
             element.classList.contains('sapMMultiComboBoxInner'))) {
            return await handleSAPMultiSelect(id, value);
        }

        // Handle dropdown input fields
        if (element.getAttribute('aria-haspopup') === 'listbox') {
            return await handleDropdownInput(id, value);
        }

        // Handle regular select elements
        if (element.tagName.toLowerCase() === 'select') {
            if (element.multiple && Array.isArray(value)) {
                Array.from(element.options).forEach(opt => opt.selected = false);
                value.forEach(val => {
                    const option = Array.from(element.options).find(opt => opt.value === val);
                    if (option) option.selected = true;
                });
            } else {
                element.value = value;
            }
            element.dispatchEvent(new Event('change', { bubbles: true }));
        } 
        // Handle textarea elements specifically
        else if (element.tagName.toLowerCase() === 'textarea') {
            element.value = '';
            element.focus();
            element.dispatchEvent(new Event('focus', { bubbles: true }));
            element.dispatchEvent(new Event('input', { bubbles: true }));
            await new Promise(resolve => setTimeout(resolve, 300));
            
            element.value = value;
            element.dispatchEvent(new Event('input', { bubbles: true }));
            element.dispatchEvent(new Event('change', { bubbles: true }));
            
            // Ensure the textarea adjusts its size if it's auto-growing
            if (element.classList.contains('sapMTextAreaGrow')) {
                element.style.height = 'auto';
                element.style.height = `${element.scrollHeight}px`;
            }
            
            element.blur();
            element.dispatchEvent(new Event('blur', { bubbles: true }));
        }
        // Handle regular text/number inputs
        else {
            await simulateTyping(element, value);
        }

        // Add tab key press for certain fields
        if (id.match(/(__input5-__clone|__cas0-__clone|__input6-__clone|__input7-__clone).*-inner/)) {
            await simulateTabKey(element);
            await new Promise(resolve => setTimeout(resolve, 300));
        }

        return true;
    } catch (error) {
        console.log(`Error setting value for ${id}:`, error);
        return false;
    }
}

function findElementInPage(id) {
    let element = document.getElementById(id);
    if (element) return element;

    const iframes = document.getElementsByTagName('iframe');
    for (let i = 0; i < iframes.length; i++) {
        try {
            const frame = iframes[i];
            const frameDoc = frame.contentDocument || frame.contentWindow.document;
            element = frameDoc.getElementById(id);
            if (element) {
                console.log(`Found element in iframe ${i}`);
                return element;
            }
        } catch (e) {
            console.log(`Cannot access iframe ${i}`);
        }
    }
    return null;
}

function waitForElement(id) {
    return new Promise((resolve) => {
        const maxAttempts = 5;
        let attempts = 0;

        const checkElement = () => {
            attempts++;
            const element = findElementInPage(id);
            
            if (element) {
                resolve(element);
            } else if (attempts < maxAttempts) {
                setTimeout(checkElement, 100);
            } else {
                resolve(null);
            }
        };

        checkElement();
    });
}

// Enhanced message listener with retry mechanism
chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
    if (request.action === "fillForm") {
        console.log("Starting enhanced form fill process...");
        
        // Create a response function that ensures we only respond once
        let hasResponded = false;
        const safeResponse = (response) => {
            if (!hasResponded) {
                hasResponded = true;
                sendResponse(response);
            }
        };

        (async () => {
            try {
                console.log("Adding rows to table");
                await addTableRows(10);
                await new Promise(resolve => setTimeout(resolve, 2000)); // Wait for rows to be added

                let filledCount = 0;
                let failedFields = [];
                
                // Wait for page to be fully loaded
                if (document.readyState !== 'complete') {
                    await new Promise(resolve => window.addEventListener('load', resolve));
                }
                
                // Initial attempt
                for (const [id, value] of Object.entries(request.data)) {
                    await new Promise(resolve => setTimeout(resolve, 200));
                    if (!(await setFieldValue(id, value))) {
                        failedFields.push([id, value]);
                    } else {
                        filledCount++;
                    }
                }
                
                // Retry failed fields
                if (failedFields.length > 0) {
                    console.log(`Retrying ${failedFields.length} failed fields...`);
                    await new Promise(resolve => setTimeout(resolve, 1000));
                    
                    for (const [id, value] of failedFields) {
                        await new Promise(resolve => setTimeout(resolve, 300));
                        if (await setFieldValue(id, value)) {
                            filledCount++;
                            const index = failedFields.findIndex(field => field[0] === id);
                            failedFields.splice(index, 1);
                        }
                    }
                }
                
                const status = failedFields.length === 0 ? "success" : "partial";
                safeResponse({
                    status,
                    filledCount,
                    failedFields: failedFields.map(f => f[0])
                });
            } catch (error) {
                console.error("Error during form fill:", error);
                safeResponse({status: "error", error: error.toString()});
            }
        })();
        
        return true; // Will respond asynchronously
    }
});

async function addTableRows(numberOfRows = 10) {
    console.log(`Adding ${numberOfRows} rows to table...`);
    
    try {
        const addButton = document.querySelector('#__button20');
        
        if (!addButton) {
            console.error('Add button not found');
            return false;
        }

        for (let i = 0; i < numberOfRows; i++) {
            console.log(`Adding row ${i + 1}/${numberOfRows}`);
            
            // Simulate mousedown
            addButton.dispatchEvent(new MouseEvent('mousedown', {
                bubbles: true,
                cancelable: true,
                view: window
            }));

            // Simulate mouseup
            addButton.dispatchEvent(new MouseEvent('mouseup', {
                bubbles: true,
                cancelable: true,
                view: window
            }));

            // Simulate click with full details
            addButton.dispatchEvent(new MouseEvent('click', {
                bubbles: true,
                cancelable: true,
                view: window,
                detail: 1
            }));

            // Trigger focus events
            addButton.dispatchEvent(new FocusEvent('focus', {
                bubbles: true,
                cancelable: true,
                view: window
            }));

            // Also try clicking the inner span
            const buttonInner = document.querySelector('#__button20-inner');
            if (buttonInner) {
                buttonInner.click();
            }

            await new Promise(resolve => setTimeout(resolve, 750)); // Increased delay
        }

        await new Promise(resolve => setTimeout(resolve, 1500));
        console.log('Finished adding rows');
        return true;
    } catch (error) {
        console.error('Error adding rows:', error);
        return false;
    }
}