'use client';

import { Button } from '@nextui-org/button';
import { Tooltip } from '@nextui-org/tooltip';
import SettingBar from './_components/SettingBar';
import Chat from './_components/Chat';
import HandsFreeMode from './_components/HandsFreeMode';
import TextMode from './_components/TextMode';
import HamburgerMenu from './_components/HamburgerMenu';
import ShareButton from './_components/SettingBar/ShareButton';
import TabButton from '@/components/TabButton';
import Image from 'next/image';
import exitIcon from '@/assets/svgs/exit.svg';
import { BsChatRightText, BsTelephone } from 'react-icons/bs';
import { useEffect, useRef, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAppStore } from '@/zustand/store';
import lz from 'lz-string';
import { playAudios } from '@/util/audioUtils';
import JournalMode from './_components/JournalMode';
import InputField from "@/app/conversation/_components/InputField";
import microphoneSVG from '@/assets/svgs/microphone.svg';
import microphoneSVGWhite from '@/assets/svgs/microphone-white.svg';


export default function Conversation() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isTextMode, setIsTextMode] = useState(true);
  const { isJournalMode, setIsJournalMode, resetJournal, resetSpeakersList } =
    useAppStore();
  const { character, getAudioList, setCharacter, clearChatContent } =
    useAppStore();
  // Websocket.
  const { socketIsOpen, sendOverSocket, connectSocket, closeSocket } =
    useAppStore();
  // Media recorder.
  const {
    mediaRecorder,
    connectMicrophone,
    startRecording,
    stopRecording,
    closeMediaRecorder,
  } = useAppStore();
  // Audio player
  const audioPlayerRef = useRef(null);
  const audioQueueRef = useRef(useAppStore.getState().audioQueue);
  const { isPlaying, setIsPlaying, popAudioQueueFront } = useAppStore();
  const { setAudioPlayerRef, stopAudioPlayback } = useAppStore();
  // Web RTC
  const {
    connectPeer,
    closePeer,
    incomingStreamDestination,
    audioContext,
    rtcConnectionEstablished,
  } = useAppStore();
  const { selectedMicrophone, selectedSpeaker } = useAppStore();
  const { vadEvents, vadEventsCallback, disableVAD, enableVAD, closeVAD } =
    useAppStore();

  useEffect(
    () =>
      useAppStore.subscribe(
        state => (audioQueueRef.current = state.audioQueue)
      ),
    []
  );

  useEffect(() => {
    const characterString = searchParams.get('character');
    const character = JSON.parse(
      lz.decompressFromEncodedURIComponent(characterString)
    );
    setCharacter(character);
    setIsJournalMode(false);
    resetJournal();
    resetSpeakersList();
  }, []);

  // Bind current audio player to state ref.
  useEffect(() => {
    setAudioPlayerRef(audioPlayerRef);
  }, []);

  useEffect(() => {
    connectSocket();
  }, [character]);

  useEffect(() => {
    if (mediaRecorder) {
      closeMediaRecorder();
    }
    if (rtcConnectionEstablished) {
      closePeer();
    }
    getAudioList()
      .then()
      .then(() => {
        connectPeer().then(() => {
          connectMicrophone();
          initializeVAD();
        });
      });
  }, [selectedMicrophone]);

  function initializeVAD() {
    if (vadEvents) {
      closeVAD();
    }
    vadEventsCallback(
      () => {
        stopAudioPlayback();
        startRecording();
      },
      () => {
        // Stops recording and send interim audio clip to server.
        sendOverSocket('[&Speech]');
        stopRecording();
      },
      () => {
        sendOverSocket('[SpeechFinished]');
      }
    );
    if (!isTextMode && !disableMic) {
      enableVAD();
    }
  }

  // Reconnects websocket on setting change.
  const {
    preferredLanguage,
    selectedModel,
  } = useAppStore();
  useEffect(() => {
    if (!mediaRecorder || !socketIsOpen || !rtcConnectionEstablished) {
      return;
    }
    closeSocket();
    clearChatContent();
    connectSocket();
    initializeVAD();
  }, [
    preferredLanguage,
    selectedModel,
  ]);

  useEffect(() => {
    // The chrome on android seems to have problems selecting devices.
    if (typeof audioPlayerRef.current.setSinkId === 'function') {
      audioPlayerRef.current.setSinkId(selectedSpeaker.values().next().value);
    }
  }, [selectedSpeaker]);

  // Audio Playback
  useEffect(() => {
    if (audioContext, !isPlaying && audioQueueRef.current?.length > 0) {
      playAudios(
        audioContext,
        audioPlayerRef,
        audioQueueRef,
        isPlaying,
        setIsPlaying,
        incomingStreamDestination,
        popAudioQueueFront
      );
    }
  }, [audioContext, audioQueueRef.current?.length]);

  const { isMute, setIsMute, disableMic, setDisableMic } = useAppStore();

  function handsFreeMode() {
    setIsTextMode(false);
    if (!disableMic) {
      enableVAD();
    }
  }

  function textMode() {
    if (isTextMode) return;
    setIsTextMode(true);
    disableVAD();
  }

  function toggleTextMode() {
    if (isTextMode && !disableMic) enableVAD();
    else disableVAD();
    setIsTextMode(!isTextMode);

  }

  function toggleMute() {
    if (!isMute) {
      stopAudioPlayback();
    }
    setIsMute(!isMute);
  }

  function handleMic() {
    if (disableMic) {
      enableVAD();
    } else {
      disableVAD();
    }
    setDisableMic(!disableMic);
  }

  const cleanUpStates = () => {
    disableVAD();
    closeVAD();
    stopAudioPlayback();
    closeMediaRecorder();
    closePeer();
    closeSocket();
    clearChatContent();
    setCharacter({});
  };

  // For journal mode
  useEffect(() => {
    if (isJournalMode) {
      enableVAD();
    } else {
      disableVAD();
    }
  }, [isJournalMode]);

  return (
      <div className="relative h-screen conversation_container">
        <audio
            ref={audioPlayerRef}
            className="audio-player"
        >
          <source
              src=""
              type="audio/mp3"
          />
        </audio>
        <div className="fixed top-0 w-full bg-purple-100 z-10">
          <div className="flex justify-between mt-4 md:mt-5 pt-2 md:pt-4 gap-5 items-center float-left">
            <div>
              <Tooltip
                  content="Exit"
                  placement="bottom"
              >
                <Button
                    isBlock
                    isIconOnly
                    radius="full"
                    className="hover:opacity-80 h-8 w-8 md:h-12 md:w-12 ml-5 mt-1 primary-bg"
                    onPress={() => {
                      router.push('/');
                      cleanUpStates();
                    }}
                >
                  <Image
                      priority
                      src={exitIcon}
                      alt="exit"
                  />
                </Button>
              </Tooltip>
            </div>
            {/*<div className="col-span-2 flex gap-5 border-2 rounded-full p-1 border-tab">*/}
            {/*  <TabButton*/}
            {/*      isSelected={isTextMode}*/}
            {/*      handlePress={textMode}*/}
            {/*      className="min-w-fit h-fit py-2 md:min-w-20 md:h-11 md:py-4"*/}
            {/*  >*/}
            {/*      <span className="md:hidden">*/}
            {/*        <BsChatRightText size="1.2em"/>*/}
            {/*      </span>*/}
            {/*    <span className="hidden md:inline">Text</span>*/}
            {/*    <span className="hidden lg:inline">&nbsp;mode</span>*/}
            {/*  </TabButton>*/}
            {/*  <TabButton*/}
            {/*      isSelected={!isTextMode}*/}
            {/*      handlePress={handsFreeMode}*/}
            {/*      className="min-w-fit h-fit py-2 md:min-w-20 md:h-11 md:py-4"*/}
            {/*  >*/}
            {/*      <span className="md:hidden">*/}
            {/*        <BsTelephone size="1.2em"/>*/}
            {/*      </span>*/}
            {/*    <span className="hidden md:inline">Hands-free</span>*/}
            {/*    <span className="hidden lg:inline">&nbsp;mode</span>*/}
            {/*  </TabButton>*/}
            {/*</div>*/}
            {/*<div className="flex flex-row justify-self-end md:hidden">*/}
            {/*  /!*<ShareButton/>*!/*/}
            {/*  <HamburgerMenu/>*/}
            {/*</div>*/}
          </div>
          <div
              className="flex flex-col mt-4 md:mt-5 pt-2 md:pt-5 pb-5 md:mx-auto md:w-unit-9xl lg:w-[892px]">
            <SettingBar
                isTextMode={isTextMode}
                isMute={isMute}
                toggleMute={toggleMute}
                disableMic={disableMic}
                handleMic={handleMic}
            />
          </div>
        </div>
        <div className="h-full -mb-24">
          <div className="h-[154px] md:h-[178px]"></div>
          {/*{!isTextMode && <div className="h-[250px] md:h-[288px]"></div>}*/}
          <div className="w-full px-4 md:px-0 mx-auto md:w-unit-9xl lg:w-[892px]">
            <Chat/>
          </div>
          <div className="h-24"></div>
        </div>
        <div className="fixed bottom-0 w-full bg-white">
          <div className="px-4 md:px-0 mx-auto md:w-unit-9xl lg:w-[892px]">
            <HandsFreeMode isDisplay={!isTextMode}/>
            <section className={`flex gap-6 items-center mb-2`}>
              <div
                  className="border-x-[1px] border-t-[1px] md:border-b-[1px] rounded-lg border-black/30 -mx-4 md:mx-0 relative flex-grow"
                  onClick={textMode}
              >
                <InputField/>
              </div>
              <div
                  className={`flex items-center justify-center w-16 h-16 rounded-full cursor-pointer ${isTextMode ? 'bg-transparent': 'bg-red-500 primary-text'}`}
                  onClick={toggleTextMode}
              >
                <Image
                    priority
                    src={isTextMode ? microphoneSVG : microphoneSVGWhite}
                    alt="microphone"
                    className="w-8 h-8"
                />
              </div>
            </section>
          </div>
        </div>
        {/*<JournalMode/>*/}
      </div>
  );
}
