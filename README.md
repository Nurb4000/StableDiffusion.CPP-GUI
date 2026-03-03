# StableDiffusion.CPP-GUI


This is a super KISS webGUI for stable diffusion.cpp tailored to what i needed, so wont I pretend its 'feature complete' for the masses.  I also wanted to keep dependencies to a bare minimum to run anywhere. So all it needs is python, flask and pillow. It can serve as a startling point for others and is easy to add more variables, so figured id share.  Future features may include up-sizing and and 'seed image' and such. But no guarantees.

It basically runs a unique canned command-line for each model, with the option for a few variables. Shows a preview of the image and will let you download it + the parameters used as a zip.  In my case, most of the time i use the same parameters for a respective model, so why clutter up the interface?  It also cleans up the image folder so you don't end up with a lot of trash in there after downloading.  

Current variables

    Model Name - this will be the ones you have configured. It does NOT scan your folder and make guesses.
    Lora Name - this will scan your folder on server start for your list. It defaults to none.
    Height and Width  - defaults  of 1024x768.
    Seed - defaults to random.
    Steps - defaults to 10 
    File name - it defaults to using the date/time.
    More may be added later, but no current plans to add more.

Its using a dark mode, but you can always change the CSS.

It currently exposes the IP to all of your network. You can change that if needed by changing the published ip from 0.0.0.0 when it calls flask, at the bottom of the code. Change the port there too. 

To run:

    Copy the SD.CPP command line binary to the root folder of the project, which can be downloaded or easily built from their instructions if they dont have a binary for you.
    Place any models and vae's you want in the model folder
    Place any loras you want to use in the lora folder. 
    Configure your models 'defaults'. Look at the section "model configs" for a few sample configurations. If you add another, it will magically appear in the choice list on a server restart.  Check the SD.CPP CLI documentation for the exhaustive list of possible parameters. 
    start the server like any other python app :     "python app.py"
    Note - If you have an older version of flask, there is a section to edit to accommodate versions lower then 2.0 so edit that as needed too.  

And an obligatory screenshot

<img width="922" height="932" alt="screenshot" src="https://github.com/user-attachments/assets/3f31ca7e-f027-4c0d-b9d6-f913770cd371" />


