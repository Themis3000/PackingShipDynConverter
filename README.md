# PackingShipDynConverter

Converts etsy packing slip pdf's into a smaller under 4 inch wide packing slip for the purpose of fitting into 4x8 envelopes with no folding

## Why?

I sell pins online (https://ThemisPins.com) and I send them 4 4x8 envelopes. I ship the pins via hand sorted letter mail (costs only $0.88 instead of the full $3.88 it would cost if I shipped as a parcel with tracking). In doing this I do need to keep the thickness of the package/"letter" under 0.25". In order to fit the pdf in its original size into the envelop I would have to fold it a total of 4 times, making it much too thick. I created this program to convert the packing slip pdf into a smaller version, reformatting the information into a layout that makes it fit without compromising the font size or overall readability.

## How?

The pdf is scraped for its information, then the program takes that information and creates a.html document containing the packing slip. All dimensions of the pdf are defined in inches, so it has a fixed width and will always print to the correct size. The height is variable, allowing the slip to be the perfect size for the content contained.

## I run an etsy shop, how can I use this?

You can either clone this repo and figure it out yourself (if you're experienced, it shouldn't be too hard to get running. You just need to install dependencies and put your packing slip in the root level of this repo and name it "in.pdf" and run main.py). If you'd like help you may open an issue on this repo, email me at mail@themimegas.com, or message me on discord @Cat Meow Meow#7380

Be sure to report any bugs or feature requests
