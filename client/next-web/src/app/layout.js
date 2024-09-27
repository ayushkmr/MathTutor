import './globals.css';
import { Prompt } from 'next/font/google';
import { Providers } from './providers';

const prompt = Prompt({
  weight: ['300', '400', '500'],
  style: ['normal', 'italic'],
  subsets: ['latin'],
});

export const metadata = {
  title: 'Math Tutor',
  description:
    'Create, customize and talk to your AI Character/Companion in realtime', // TODO: update this
};

export default function RootLayout({ children }) {
  return (
    <html lang='en' className=' h-full'>
      <body className={prompt.className + ' h-full'}>
        <Providers>
          <main>{children}</main>
        </Providers>
      </body>
    </html>
  );
}
