
const axios = require('axios');

const options = {
  method: 'POST',
  url: 'https://chatgpt-api8.p.rapidapi.com/',
  headers: {
    'content-type': 'application/json',
    'X-RapidAPI-Key': 'b262a22443msh09fce8bb1e138acp14a425jsn1dbcfc8a6b4c',
    'X-RapidAPI-Host': 'chatgpt-api8.p.rapidapi.com'
  },
  data: [
    {
      content: 'give me a detailed explanation why in this config 4kbnr/r3ppp1/p1n5/q6p/3P4/2P4B/PP1N1PPP/R1BQKBNR b KQk - 0 9 move a5c7 has the highest score. also consider the opponents moves and try to find the name of the enemies execute if any',
      role: 'user'
    }
  ]
};

async function run() {
  try {
    const response = await axios.request(options);
    console.log(response.data);
  } catch (error) {
    console.error('Error occurred:', error.message);
  }
}

run();

    