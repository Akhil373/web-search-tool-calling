import React, { useEffect, useRef, useState } from "react"
import ChatInterfance from "../components/ChatInterface"
import TopBar from "../components/TopBar"

function App() {
    const [text, setText] = useState("")
    const textareaRef = useRef(null)

    const [messages, setMessages] = useState([])
    const [clearing, setClearning] = useState(false)

    const fetchData = async (userPrompt, messageId) => {
        const url = 'http://127.0.0.1:8000/generate';
        const dataToSend = { prompt: userPrompt };

        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(dataToSend),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(`HTTP error! Status: ${response.status} - ${errorData.error || response.statusText}`);
            }

            const reader = response.body.getReader()
            const decoder = new TextDecoder()
            let full = '';
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                full += decoder.decode(value, { stream: true });
                setMessages(prev => prev.map(m =>
                    m.id === messageId ? { ...m, text: full } : m
                ));
            }
        } catch (err) {
            console.error("Error fetching data:", err);
            setMessages(prevMessages => prevMessages.map(msg =>
                msg.id === messageId ? {...msg, text: "Sorry, I ran into an error."} : msg
            ))
        }
    };

    const adjustHeight = () => {
        const textarea = textareaRef.current
        if (textarea) {
            textarea.style.height = "auto"
            const maxHeight = 200
            const newHeight = Math.min(textarea.scrollHeight, maxHeight)
            textarea.style.height = `${newHeight}px`
            if (textarea.scrollHeight > maxHeight) {
                textarea.style.overflowY = "auto"
            } else {
                textarea.style.overflowY = "hidden"
            }
        }
    }

    useEffect(() => {
        adjustHeight()
    }, [text])

    const handleChange = (e) => {
        setText(e.target.value)
    }

    const handleKeyDown = async (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            const userMsgText = text.trim();
            if (userMsgText) {
                const newUserMsg = {
                    id: Date.now(),
                    text: userMsgText,
                    sender: "You"
                }

                const aiMsgId = Date.now() + 1
                const newAiMsg = {
                    id: aiMsgId,
                    text: "Thinking...",
                    sender: "AI"
                }

                setMessages((prevMessages => [...prevMessages, newUserMsg, newAiMsg]))
                setText('')

                fetchData(userMsgText, aiMsgId)
            }
        }
    };

    const handleClearChat = () => {
        setClearning(true)
        setTimeout(() => {
            setMessages([])
            setClearning(false)
        }, 300)
    }

    return (
        <>
            <div className="flex flex-col items-center justify-center w-screen h-screen p-5 py-10 md:p-10" data-theme="forest">
            <TopBar clearChat={handleClearChat}/>
                <ChatInterfance msgs={messages} clear={clearing} />

                <textarea
                    ref={textareaRef}
                    value={text}
                    onChange={handleChange}
                    onKeyDown={handleKeyDown}
                    placeholder="Chat with Internet"
                    className={`text textarea textarea-md md:textarea-lg bg-white/5 backdrop-blur-xl shadow-2xl transition-all w-[50%] md:w-[30%] focus:md:w-[75%] focus:lg:w-[60%] focus:w-full mt-1.5 ease-in-out duration-600 resize-none rounded-2xl focus:outline-none focus:border-gray-700 border border-white/30
                    ${messages.length>0 ? "md:w-[75%] lg:w-[60%] w-full" : null}
                        `}
                    style={{
                        minHeight: "3rem",
                        height: "3rem",
                        overflowY: "hidden",
                    }}
                ></textarea>
            </div>
        </>
    )
}

export default App
