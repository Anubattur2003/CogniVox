import React from "react";
import LanguageIcon from "@mui/icons-material/Language";
import SchoolIcon from "@mui/icons-material/School";
import FunctionsIcon from "@mui/icons-material/Functions";
import CreateIcon from "@mui/icons-material/Create";
import PlayCircleOutlineIcon from "@mui/icons-material/PlayCircleOutline";
import GroupsIcon from "@mui/icons-material/Groups";

interface FocusModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const FocusModal: React.FC<FocusModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  const options = [
    {
      icon: <LanguageIcon className="text-cyan-500" />,
      title: "Web",
      description: "Search across the internet",
    },
    {
      icon: <SchoolIcon className="text-purple-500" />,
      title: "Academic",
      description: "Find academic papers",
    },
    {
      icon: <FunctionsIcon className="text-green-500" />,
      title: "Math",
      description: "Solve equations",
    },
    {
      icon: <CreateIcon className="text-yellow-500" />,
      title: "Writing",
      description: "Generate text & chat",
    },
    {
      icon: <PlayCircleOutlineIcon className="text-red-500" />,
      title: "Video",
      description: "Watch videos",
    },
    {
      icon: <GroupsIcon className="text-blue-500" />,
      title: "Social",
      description: "Find discussions",
    },
  ];

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="relative bg-[#1F1F1F] rounded-xl shadow-xl w-full max-w-md border border-white/10">
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-3 right-3 text-gray-400 hover:text-gray-200 p-1"
        >
          ✕
        </button>

        {/* Modal content */}
        <div className="p-4">
          <h2 className="text-lg text-gray-200 mb-3">Choose Focus</h2>

          <div className="grid grid-cols-2 gap-2">
            {options.map((option, index) => (
              <button
                key={index}
                className="flex flex-col p-1 rounded-lg hover:bg-white/5 transition-colors duration-200 border border-white/5"
              >
                <div className="flex items-center gap-2 mb-1">
                  {option.icon}
                  <span className="text-gray-200 text-sm font-medium">
                    {option.title}
                  </span>
                </div>
                <p className="text-xs text-gray-400 text-left">
                  {option.description}
                </p>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default FocusModal;
