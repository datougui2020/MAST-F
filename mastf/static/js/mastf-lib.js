
REST = {
    doGet: function(url, onsuccess, error = null) {
        REST.ajax(url, 'GET', null, onsuccess, null, error);
    },

    post: function(url, data, onsuccess, contentType = "application/json", error = null) {
        REST.ajax(url, 'POST', data, onsuccess, contentType, error);
    },

    patch: function(url, data, onsuccess, contentType = "application/json", error=null) {
        REST.ajax(url, 'PATCH', data, onsuccess, contentType, error);
    },

    delete: function(url, onsuccess, contentType = "application/json") {
        REST.ajax(url, 'DELETE', null, onsuccess, contentType);
    },

    del: function(url, onsuccess, data, contentType = "application/json") {
        REST.ajax(url, 'DELETE', data, onsuccess, contentType);
    },

    ajax: function(url, method, data = null, onsuccess = null, contentType = "application/json", error = null) {
        if (error == null) {
            error = function(data) {
                if (data.detail) {
                    Alerts.show("error", "Unexpected Error", data.detail);
                    fadeOutMessages();
                }
            };
        }
        $.ajax(url, {
            method: method,
            success: onsuccess,
            data: data,
            contentType: contentType,
            error: error,
            headers: {
                'X-CSRFToken': csrftoken
            }
        })
    },
}

Utils = {
    getValue: function(selector) {
        if (!selector.startsWith("#")) {
            selector = '#' + selector;
        }

        element = $(selector);
        if (selector === undefined) {
            // Display error messages (NOT IMPLEMENTED)
            console.error("Could not locate Element: " + selector);
            return null;
        }
        return element.attr('value');
    },

    isDarkLaf: function() {
        classAttr = document.body.getAttribute("class");
        if (classAttr == null) {
            return false;
        }
        return classAttr.includes("theme-dark");
    },

    escapeHTML: function(html) {
        var text = document.createTextNode(html);
        var p = document.createElement('p');
        p.appendChild(text);
        return p.innerHTML;
    },

    capitalize: function(text) {
        return text.charAt(0).toUpperCase() + text.slice(1);
    },

    convertParams: function(params) {
        var result = {};
        if (!params) return result;

        params = params.split('&');
        for (var i = 0; i < params.length; i++) {
          var parts = params[i].split('=');
          result[parts[0]] = decodeURIComponent(parts[1]).replace(/\+/g, ' ');
        }
        return result;
    },

    /**
     * Applies a progress bar color and width according to the
     * provided severity.
     *
     * @param {string} severity the current severity string
     */
    setSeverity(severity, bar, badge) {
        badge.html(severity);
        switch (severity.toLowerCase()) {
            case "high":
                bar.attr("style", "width: 80%");
                bar.attr("class", "progress-bar bg-red");
                badge.attr("class", "badge bg-red-lt");
                break;

            case "critical":
                bar.attr("style", "width: 100%");
                bar.attr("class", "progress-bar bg-pink");
                badge.attr("class", "badge bg-pink-lt");
                break;

            case "medium":
                bar.attr("style", "width: 50%");
                bar.attr("class", "progress-bar bg-orange");
                badge.attr("class", "badge bg-orange-lt");
                break;

            case "low":
                bar.attr("style", "width: 30%");
                bar.attr("class", "progress-bar bg-yellow");
                badge.attr("class", "badge bg-yellow-lt");
                break;

            default:
                bar.attr("style", "width: 0%");
                bar.attr("class", "progress-bar bg-secondary");
                badge.attr("class", "badge bg-secondary-lt");
                break;
        }
    },

    permissionColors: {
        'SIGNATURE': "green",
        'SIGNATUREORSYSTEM': "green",
        'KNOWNSIGNER': "green",
        'RUNTIME': "green",
        'DANGEROUS': "red",
        'SYSTEM': "red",
        'OEM': "red",
        'PRIVILEGED': "red",
        'VENDORPRIVILEGED': "red",
        'NORMAL': "azure",
        'COMPANION': "azure",
        'CONFIGURATOR': "azure",
        'PRE23': "azure",
    }
}

/**
 * Simple object that defines utility methods when loading information
 * on a single vulnerability. By calling the "load" function, template
 * details, veulnerability details and the target source code will be
 * fetched from the REST API
 */
FindingView = {
    load: function(element, interface) {
        template_id = Utils.getValue(interface.makeTemplateId(element.getAttribute('counter')));
        finding_id = Utils.getValue(interface.makeFindingId(element.getAttribute('counter')));
        scanner_name = Utils.getValue(interface.scanner_id);
        scan_id = Utils.getValue(interface.scan_id);

        REST.doGet("/api/v1/finding/template/" + template_id, interface.handleTemplateData);
        REST.doGet(interface.makeFindingURL(finding_id), interface.handleFindingData);
        REST.doGet("/api/v1/code/" + finding_id, interface.handleCode);

        interface.rootElement.fadeIn("slow");
    },

    hide: function(interface) {
        interface.rootElement.attr("style", "display: none;");
        interface?.onClose();
    },
};

Vulnerability = {

    scanner_id: "scanner-name",
    scan_id: "scan-id",
    rootElement: $('#vuln-card'),

    makeTemplateId: function(counter) {
        return 'vuln-template-id-row-' + counter;
    },

    makeFindingId: function(counter) {
        return 'vuln-id-row-' + counter;
    },

    makeFindingURL: function(findingId) {
        return "/api/v1/finding/vulnerability/" + findingId
    },

    handleTemplateData: function(data) {
        document.getElementById('vuln-info-text').innerHTML = data.description;

        title = $('#vuln-title');
        title.html(data.title);
        title.attr('href', "/web/details/" + data.article);
    },

    handleFindingData: function(data) {
        Utils.setSeverity(data?.severity, $('#vuln-severity'), $('#vuln-severity-badge'));
        $('#vuln-details-dropdown').html(data?.state);
        $('#vuln-language').html(data?.snippet?.language);
        $('#vuln-details-file-size').html(data?.snippet?.file_size);
        $('#vuln-details-language').html(data?.snippet?.language);
        $('#vuln-details-lines').html(data?.snippet?.lines);
        $('#vuln-id').attr('value', data.finding_id);
    },

    handleCode: function(data) {
        $('#vuln-code').html(data?.code || "Not Found");

        let theme_name = 'enlighter';
        if (Utils.isDarkLaf()) {
            theme_name = 'dracula';
        }

        if (data != null) {
            EnlighterJS.init('pre', 'code.vuln_code', {
                language : data?.language.toLowerCase(),
                theme: theme_name,
                indent : 2,
                textOverflow: 'scroll'
            });
        }
    },

    applyVulnerabilityState: function(element) {
        findingId = Utils.getValue('vuln-id');
        target = document.getElementById('vuln-details-dropdown');

        if (target.innerHTML == element.innerHTML) {
            return;
        }

        REST.patch("/api/v1/finding/vulnerability/" + findingId, JSON.stringify({
            finding_id: findingId,
            state: element.innerHTML
        }), function(data) {
            if (data.success) {
                target.innerHTML = element.innerHTML;
                document.getElementById("vuln-state-row-" + findingId).innerHTML = element.innerHTML;
            } // TODO: add logging
        })
    },

    onClose: function() {
        $('#vuln-severity').attr("style", "width: 0%;");
    },
};

Finding = {
    scanner_id: "scanner-name",
    scan_id: "scan-id",
    rootElement: $('#finding-card'),

    makeTemplateId: function(counter) {
        return 'finding-template-id-row-' + counter;
    },

    makeFindingId: function(counter) {
        return 'finding-id-row-' + counter;
    },

    makeFindingURL: function(findingId) {
        return "/api/v1/finding/" + findingId
    },

    handleTemplateData: function(data) {
        document.getElementById('finding-info-text').innerHTML = data.description

        title = $('#finding-title')
        title.html(data.title);
        title.attr('href', "/web/details/" + data.article);
    },

    handleFindingData: function(data) {
        Utils.setSeverity(data?.severity, $('#finding-severity'), $('#finding-severity-badge'));
        $('#finding-language').html(data?.snippet?.language);
        $('#finding-details-file-size').html(data?.snippet?.file_size);
    },

    handleCode: function(data) {
        $('#finding-code').html(data?.code || "Not Found");

        let theme_name = 'enlighter';
        if (Utils.isDarkLaf()) {
            theme_name = 'dracula';
        }

        EnlighterJS.init('pre', 'code.finding_code', {
            language : data.language.toLowerCase(),
            theme: theme_name,
            indent : 2,
            textOverflow: 'scroll'
        });
    },

    onClose: function() {
        $('#finding-severity').attr("style", "width: 0%;");
    },
}

Alerts = {
    show: function(level, title, message) {
        var div = document.createElement("div");
        div.classList.add("alert", `alert-${level.toLowerCase()}`, "alert-dismissable", "mb-2");

        let icon = '<svg xmlns="http://www.w3.org/2000/svg" class="icon alert-icon" width="24" height="24" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" fill="none" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M12 12m-9 0a9 9 0 1 0 18 0a9 9 0 1 0 -18 0" /><path d="M12 8l0 4" /><path d="M12 16l.01 0" /></svg>';
        div.innerHTML = `<div class="d-flex"><div>${icon}</div><div><h4 class="alert-title">${title}</h4><div class="text-muted">${message}</div></div></div>`;

        document.getElementById("alert-container").appendChild(div);
    },
}

Severity = {
    'critical': 'pink',
    'high': 'red',
    'medium': 'orange',
    'low': 'yellow',
    'info': 'azure',
    'secure': 'green',
    'none': 'secondary'
};

/**
 * Utility module to enable a wizard-like view in a modal. This code
 * should be used together with the CSS 'steps' class. It can be used
 * as follows:
 *
 * <div class="steps">
 *  <a href="#" id="mysteps-step-0" step="0" onclick="Steps.showStep(this, 'mysteps');">
 *      First step
 *  </a>
 *  <a href="#" id="mysteps-step-1" step="1" onclick="Steps.showStep(this, 'mysteps');">
 *      Second step
 *  </a>
 * </div>
 *
 * Actually, the content for each step can be placed anywhere in the HTML
 * document, it just has to be marked with a special ID:
 *
 * <div id="mysteps-content-step-0">...</div>
 * <div id="mysteps-content-step-1" style="display: none;">...</div>
 *
 * Call Steps.reset(prefix) to reset the state of all steps.
 */
Steps = {

    showStep: function(element, prefix) {
        // First, we have to make sure the step has been enabled.
        if (element.getAttribute("class").includes("disabled")) {
            return;
        }

        contentId = element.getAttribute("step");
        oldContent = Steps.activeStepContent(prefix);
        oldStep = Steps.activeStep(prefix);

        if (oldStep != null) {
            $(oldStep).removeClass("active");
        }

        newContent = $('#'+ prefix + '-content-step-' + contentId);
        if (oldContent != null) {
            $(oldContent).fadeOut(400, function() {
                newContent.fadeIn();
            });
        }
        else {
            console.log(oldContent);
            newContent.fadeIn('slow');
        }


        $(element).addClass("active");
    },

    nextStep: function(element, prefix) {
        step = Steps.activeStep(prefix);

        if (step.getAttribute("class").includes("disabled")) {
            return;
        }

        contentId = parseInt(step.getAttribute("step")) + 1;
        newStep = document.getElementById(prefix + '-step-' + contentId);
        if (newStep === undefined) {
            console.log('Could not find next step');
            return;
        }

        // make sure the step is not disabled
        $(newStep).removeClass("disabled");

        Steps.showStep(newStep, prefix);
        elementId = element.getAttribute("step-showonfinish");
        if (elementId != null && newStep.getAttribute("step-end") == "true") {
            $(element).fadeOut(100, function() {
                $('#' + elementId).fadeIn();
            });
        }
    },

    reset: function(prefix) {
        for (let element of Steps.getStepContents(prefix)) {
            if (element.id == prefix + "-content-step-0") {
                $(element).fadeIn();
            }
            else {
                $(element).attr("style", "display: none;");
            }
        }
        for (let element of $("[id^=" + prefix + "-step]")) {
            if (element.id == prefix + "-step-0") {
                $(element).addClass('active');
            }
            else {
                $(element).addClass('disabled');
                $(element).removeClass('active');
            }
        }

        nextStepElement = document.getElementById(prefix + '-next-step');
        elementId = nextStepElement.getAttribute("step-showonfinish");
        if (elementId != null) {
            $('#' + elementId).fadeOut(100, function() {
                $(nextStepElement).fadeIn();
            });
        }
    },

    getStepContents: function(prefix) {
        return $("[id^=" + prefix + "-content]");
    },

    activeStepContent: function(prefix) {
        elements = Steps.getStepContents(prefix);
        for (let element of elements) {
            var style = element.getAttribute("style");
            if (style == null || !style.includes("display: none;")) {
                return element;
            }
        }
        return null;
    },

    activeStep: function(prefix) {
        var elements = $("[id^=" + prefix + "-step]");

        for (let element of elements) {
            if (element.getAttribute("class")?.includes("active")) {
                return element;
            }
        }
        return null;
    },

}

class Tags {

    constructor(prefix, areaElement, inputElement, options) {
        this.prefix = prefix
        this.inputElement = inputElement
        this.areaElement = areaElement
        this.count = 0

        var options = options || {}
        this.keys = options.keys || [13, 32, 44]
        this.buildKBD = options.onCreateKbd || this.onCreateKbd

        var ref = this;
        $(inputElement).keydown(function(event) {
            if (ref.keys.includes(event.keyCode)) {
                event.preventDefault();
                ref.create();
            }
            else if (event.keyCode == 8) {
                let input = $(ref.inputElement)
                var text = input.val();

                if (text.trim().length == 0) {
                    event.preventDefault();
                    let id = `${ref.prefix}-${ref.count}`
                    let element = $('#' + id);

                    if (element != null) {
                        ref.count--;
                        element.remove();
                    }
                }
            }
        })
    }

    onCreateKbd(text) {
        this.count++;
        const kbd = document.createElement("kbd");
        kbd.id = `${this.prefix}-${this.count}`;
        kbd.innerHTML = text;
        kbd.style.marginRight = "3px";
        kbd.style.cursor = "no-drop";
        return kbd;
    }

    create() {
        let input = $(this.inputElement)
        var text = input.val().trim();
        if (text.length == 0) {
            return
        }

        var kbdHTML = this.buildKBD(text);
        this.areaElement.appendChild(kbdHTML);
        input.val("");

        let self = this;
        $(kbdHTML).on("click", function(event) {
            self.count--;
            $(event.target).remove();
        });
    }

}



