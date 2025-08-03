import React from "react"

const TopBar = ({clearChat}) => {
    return (
        <nav className="fixed top-5 right-10">
            <button onClick={clearChat} className="btn max-w-fit bg-red-700/50">
                Clear Chat
            </button>

            <div className="dropdown">
                <div tabIndex={0} role="button" className="btn m-1">
                    Theme
                </div>
                <ul
                    tabIndex={0}
                    className="dropdown-content menu bg-base-100 rounded-box z-1 w-52 p-2 shadow-sm"
                >
                    <li>
                        <a>Item 1</a>
                    </li>
                    <li>
                        <a>Item 2</a>
                    </li>
                </ul>
            </div>
        </nav>
    )
}

export default TopBar
