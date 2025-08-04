const TopBar = ({ clearChat }) => {

  return (
    <nav className="fixed top-5 right-10 flex items-center gap-4">
      <button
        onClick={clearChat}
        className="btn max-w-fit bg-red-700/50"
      >
        Clear Chat
      </button>
    </nav>
  );
};

export default TopBar;