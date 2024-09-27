const host = process.env.API_HOST;

export async function getCharacters() {
  try {
    const res = await fetch(`${host}/characters`, { next: { revalidate: 5 } });
    const characters = await res.json();
    console.log('getCharacters: got ' + characters.length + ' characters');
    console.log('chars: test');
    return characters; //.filter(chars => chars.character_id === 'annie');
  } catch (err) {
    console.log('getCharacters - Error: ' + err);
    return [];
  }
}
