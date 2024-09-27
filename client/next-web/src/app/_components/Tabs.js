'use client';
import ExploreTab from './ExploreTab';
import MyTab from './MyTab';
import TabButton from '@/components/TabButton';

import { useAuthContext } from '@/context/AuthContext';
import { useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { useAppStore } from '@/zustand/store';

export default function Tabs({ characters }) {
  const { user } = useAuthContext();
  const { tabNow, setTabNow } = useAppStore();
  const searchParams = useSearchParams();

  useEffect(() => {
    const tab = searchParams.get('tab') || 'topics';
    if (tab) {
      setTabNow(tab);
    }

  }, []);

  function charactersShown(tab) {
    return characters;
  }

  return (
    <>
      <div className='flex flex-row justify-center mt-10'>
        <div className='w-[630px] flex gap-5 border-2 rounded-full p-1 border-tab primary-text'>
          <TabButton isSelected={tabNow === 'topics'} handlePress={() => setTabNow('topics')}>
            Topics
          </TabButton>
          <TabButton
            isSelected={user && tabNow === 'fav'}
            isDisabled={user == null}
            handlePress={() => setTabNow('fav')}
          >
            Favourites
          </TabButton>
        </div>
      </div>
      <ExploreTab
        characters={charactersShown(tabNow)}
        isDisplay={tabNow !== 'fav'}
      />
      {user && <MyTab isDisplay={tabNow === 'fav'} />}
    </>
  );
}
