import React from "react"
import Markdown from "react-markdown"

const ChatInterfance = ({msgs, clear}) => {
    return (
        <div className="flex items-start justify-center w-full h-full pt-10 md:pt-15 md:px-20">
            <div className="flex flex-col w-full h-full max-w-3xl space-y-3 overflow-y-auto">
                {msgs.length === 0 ? (
                    <div className="flex justify-center items-center h-full md:text-3xl text-2xl opacity-50 px-10">
                        Hello! Start searching the Web.
                    </div>
                ) : (
                    msgs.map((msg) => (
                        <React.Fragment key={msg.id}>
                            <div
                                className={` 
                                        ${
                                            msg.sender === "You"
                                                ? "self-end"
                                                : null
                                        }`}
                            >
                                {msg.sender}
                                <span className="block mt-1 text-xs text-gray-400">
                                    {new Date(msg.id).toLocaleTimeString([], {
                                        hour: "2-digit",
                                        minute: "2-digit",
                                    })}
                                </span>
                            </div>
                            <div
                                className={`p-[12px] rounded-2xl transition-all duration-500 ease-in-out ${
                                    msg.sender === "You"
                                        ? "bg-blue-950/70 self-end max-w-[80%]"
                                        : "self-start w-full align-center"
                                } ${
                                    clear
                                        ? "opacity-0 -translate-x-full"
                                        : "opacity-100 translate-x-0"
                                } ${
                                    msg.text === "Thinking..."
                                        ? "animate-pulse"
                                        : null
                                }
                                    `}
                            >
                                <Markdown>{msg.text}</Markdown>
                            </div>
                        </React.Fragment>
                    ))
                )}
            </div>
        </div>
    )
}

export default ChatInterfance
