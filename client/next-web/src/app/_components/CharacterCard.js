import {
  Card,
  CardBody,
  CardFooter,
  Avatar,
  Button
} from '@nextui-org/react';
import { FaPlay, FaStop } from 'react-icons/fa';
import Image from 'next/image';
import audioSvg from '@/assets/svgs/audio.svg';
import { useRouter } from 'next/navigation';
import lz from 'lz-string';

export default function CharacterCard({
  character,
  playingId,
  handlePlay
}) {
  const router = useRouter();
  const isPlaying = playingId == character.character_id;

  function handlePress() {
    return handlePlay(character.character_id, character.audio_url);
  }

  return (
    <Card className="p-2.5 bg-white">
        <CardBody className="p-0 text-center flex-row gap-2 md:flex-col">
          <iframe width="500" height="300" src="https://www.youtube.com/embed/NVhA7avdTAw?rel=0"
                  title="Introduction to multiplication" frameBorder="0"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                  referrerPolicy="strict-origin-when-cross-origin" className="rounded-xl" allowFullScreen></iframe>
        </CardBody>
        <CardFooter className="mt-2">
            <Button
                className="w-full primary-bg font-light hover:opacity-80"
                onPress={() => {
                    const compressedCharacter = lz.compressToEncodedURIComponent(
                        JSON.stringify(character)
                    );
                    router.push(`/conversation?character=${compressedCharacter}`);
                }}
            >Let&apos;s Practice!</Button>
      </CardFooter>
    </Card>
  );
}
