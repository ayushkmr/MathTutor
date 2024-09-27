import SpeakerControl from './SpeakerControl';
import MicrophoneControl from './MicrophoneControl';
import LanguageModelControl from './LanguageModelControl';
import ShareButton from './ShareButton';
import SettingsButton from './SettingsButton';
import { Avatar } from '@nextui-org/avatar';
import { useAppStore } from '@/zustand/store';
import { FaExternalLinkAlt } from "react-icons/fa";
import HamburgerMenu from "@/app/conversation/_components/HamburgerMenu";

export default function SettingBar({
  isTextMode,
  isMute,
  toggleMute,
  disableMic,
  handleMic,
}) {
  const { character } = useAppStore();

  return (
      <div className={`flex flex-row px-4 justify-between`}>
          <div className="flex gap-1 items-center">
              <Avatar
                  name={character.name}
                  src={character.image_url}
              />
              <span className="pl-2">{character.name}</span>
              <div className="flex">
                  <SpeakerControl
                      isMute={isMute}
                      toggleMute={toggleMute}
                  />
                  {!isTextMode && (
                      <MicrophoneControl
                          isDisabled={disableMic}
                          handleMic={handleMic}
                      />
                  )}
              </div>
          </div>
          <div className="hidden gap-8 md:flex">
              {/*<LanguageModelControl />*/}
              {/*<ShareButton />*/}
              <SettingsButton/>
          </div>
          <div className="flex flex-row justify-self-end md:hidden">
              <HamburgerMenu/>
          </div>
      </div>
  );
}
