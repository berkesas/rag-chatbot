jQuery(document).ready(function ($) {
    const observer = new MutationObserver(function (mutationsList, observer) {
        // for (let mutation of mutationsList) {
        //     // console.log(mutation);
        //     if (mutation.type === 'childList') {
        //         for (let node of mutation.addedNodes) {
        //             // console.log(node.id);
        //             if (node.id != undefined) {
        //                 if (node.id.substring(0, 6) === "server") {
        //                     typeWriter();
        //                 }
        //             }
        //         }
        //     }
        // }
    });

    // const chatApi = 'http://10.10.193.224:5001/api/chattest';
    const chatApi = 'http://10.10.193.224:5001/api/chat';

    let introduced = false;
    let chatVisible = false;
    let loading = false;
    let currentId = 0;

    let currentCharIndex = 0;
    let currentTxt = '';
    let currentBox = 'msg';
    const speed = 50;
    let chunkSize = 3;

    const dateFormatOptions = {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
    };

    $('#chatWindow').hide();
    $('#divLoading').hide();

    $('#btnChat').click(function () {
        toggleChat();
    });

    $('#btnClose').click(function () {
        toggleChat();
    });

    $("#btnSend").click(function () {
        askQuestion();
    });

    window.askProposedQuestion = function (question, auto_submit = true) {
        $("#txtQuestion").val(question);
        if (auto_submit) {
            askQuestion();
        }
    }

    $("#txtQuestion").keydown(function (event) {
        if (event.keyCode === 13 && event.shiftKey) {
            event.preventDefault();
            $("#txtQuestion").val($("#txtQuestion").val() + "\n");
            return;
        }
        if (event.keyCode === 13) {
            event.preventDefault();
            askQuestion()
        }
    });

    // Start observing the target node for configured mutations
    const config = { childList: true, subtree: true };
    observer.observe(document.getElementById('chatHistory'), config);

    function toggleChat() {
        $('#chatWindow').fadeToggle(200);
        $('#chatBubble').fadeToggle(200);
        chatVisible = !chatVisible;
        if (chatVisible) introduceBot();
    }

    function introduceBot() {
        if (introduced) return;
        const msg = {
            "source": 'server',
            "text": "Hello my name is Virtual Chat Agent. You can ask me questions.",
            "created": new Date(),
            "additionalQuestions": []
        };

        addMessage(msg);
        introduced = true;
    }

    function askQuestion() {
        let question = $("#txtQuestion").val();
        if (question !== "") {
            const msg = {
                "source": "user",
                "text": question
            }
            addMessage(msg);
            sendToServer(msg, chatApi);
            $("#txtQuestion").val('');
        } else {
            console.log("Question cannot be empty");
        }
    }

    function sendToServer(msg, chatApi) {
        $('#divLoading').show();
        scrollMessages();
        $.ajax({
            url: chatApi,
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify(msg),
            success: function (response) {
                console.log("Response:", response);
                addMessage(response[0]);
                $('#divLoading').hide();
                scrollMessages();
            },
            error: function (xhr, status, error) {
                const msg = {
                    "source": 'server',
                    "text": "Sorry, there was an error.",
                    "created": new Date(),
                    "additionalQuestions": []
                };
                addMessage(msg);
                console.error("Error:", error);
                $('#divLoading').show();
                scrollMessages();
            }
        });
    }

    function addMessage(msg) {
        let newMessage = "";
        if (msg['source'] == "server") {
            newMessage = getServerMessageCode(currentId, msg);
            // initiateTypeWriter(msg, currentId);
        }
        else {
            newMessage = getUserMessageCode(currentId, msg);
        }
        $("#chatHistory").append(newMessage);
        currentId++;
    }


    function scrollMessages() {
        let div = $("#chatList");
        div.scrollTop(div[0].scrollHeight);
    }

    // function initiateTypeWriter(msg, currentId) {
    //     currentBox = 'msg' + currentId;
    //     currentCharIndex = 0;
    //     currentTxt = msg['text'];
    //     chunkSize = Math.floor(currentTxt.length / speed);
    //     console.log(currentBox, currentCharIndex, currentTxt);
    // }

    // function typeWriter() {
    //     if (currentCharIndex + chunkSize < currentTxt.length) {
    //         document.getElementById(currentBox).innerHTML += currentTxt.substring(currentCharIndex, currentCharIndex + chunkSize);
    //         currentCharIndex += chunkSize;
    //         setTimeout(typeWriter, speed);
    //     } else {
    //         document.getElementById(currentBox).innerHTML = currentTxt;
    //     }
    //     scrollMessages();
    // }

    function preprocess_message(text) {
        // text = text.replace(/<(.*?)>/g, '<a href="$1" class="text-blue-500 underline" target="_blank">$1</a>');
        // text = text.replace(/\[(.*?)\](.*?)\)/g, '<a href="$2" class="text-blue-500 underline" target="_blank">$2</a>')
        return text.replace('\n', '<br>');
    }

    function getServerMessageCode(id, message) {
        proposed_questions = message.additionalQuestions.map((val, index) =>
            `<div class="flex my-1"><div onclick="askProposedQuestion('` + val + `')"
                    class="cursor-pointer bg-white hover:bg-slate-100 border rounded-xl p-1 px-2 text-xs">
                    `+ val + `
            </div></div>`
        ).join('');


        return `<li id="server` + id + `">
            <div class="flex mt-2 gap-x-2"> 
                <div class="w-full">
                    <div id="msg`+ id + `" class="w-full whitespace-normal text-wrap break-normal rounded-lg bg-gray-100 p-3">
                        `+ preprocess_message(message.text) + `
                    </div>
                    <div class="flex justify-end text-xs px-2 text-gray-400">`+ (new Date()).toLocaleTimeString('en-US', dateFormatOptions) + `
                    </div>
                    `+ proposed_questions + `
                </div>
                <div><img src="chatbot-avatar.png" width="50"></div>
            </div>
            </li>`;
    }

    function getUserMessageCode(id, message) {
        return `<li id="user` + id + `" >
            <div class="flex mt-2 gap-x-2">
                <div>
                    <svg xmlns="http://www.w3.org/2000/svg" width="25" height="25" fill="currentColor" class="bi bi-person-circle" viewBox="0 0 16 16">
                        <path d="M11 6a3 3 0 1 1-6 0 3 3 0 0 1 6 0"/>
                        <path fill-rule="evenodd" d="M0 8a8 8 0 1 1 16 0A8 8 0 0 1 0 8m8-7a7 7 0 0 0-5.468 11.37C3.242 11.226 4.805 10 8 10s4.757 1.225 5.468 2.37A7 7 0 0 0 8 1"/>
                    </svg>
                </div>
                <div class="w-full">
                    <div class="w-full rounded-lg bg-gray-100 p-3">` + message.text.replace('\n', '<br>') + `</div>
                    <div class="flex justify-end text-xs px-2 text-gray-400"><button onclick="askProposedQuestion('`+ message.text.replace('\n', ' ') + `', false);">Edit</button>&nbsp;&nbsp;&nbsp;<button onclick="askProposedQuestion('` + message.text.replace('\n', ' ') + `', true);">Resubmit</button>&nbsp;&nbsp;&nbsp;` + (new Date()).toLocaleTimeString('en-US', dateFormatOptions) + `
                    </div>
                </div>
            </div>
            </li>`;
    }
});