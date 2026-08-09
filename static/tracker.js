const container = document.getElementById("anime-container");

function moveRight() {

    container.scrollBy({
        left: 300,
        behavior: "smooth"
    });

}

function moveLeft() {
    console.log("LEFT CLICKED");

    
    container.scrollBy({
        left: -300,
        behavior: "smooth"
    });
    
}