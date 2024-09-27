import Tabs from './_components/Tabs';
import Header from './_components/Header';
import Footer from './_components/Footer';

import { getCharacters } from '../util/apiSsr';

export default async function Page() {
  const characters = await getCharacters();
  console.log('chars in page:', characters);

  return (
    <>
      <Header />
      <div className='py-6 md:py-10 px-4 md:px-6 lg:px-14 container mx-auto'>
        <Tabs characters={characters} />
      </div>
      <Footer />
    </>
  );
}
