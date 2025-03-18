//Preloader
function showPreloader(event) {
  if (navigator.onLine) {
    $(".pre-loader").css("display", "flex");
    $(".pre-loader").show();

    window.onpageshow = function (event) {
        if (event.persisted) {
          $(".pre-loader").hide();
        }
    };
  } else {
    event.preventDefault();
    alert('You are currently offline. Please check your internet connection.');
  }
}

const headerTag = document.querySelectorAll("header");
const formTag = document.querySelector(".FormPage");
const chatIcon = document.querySelector('.chat-icon');
const chatCategories = document.querySelector('#popUP-content');





// Sign in password input field hide * show password
// const passwordToggle = document.getElementById('eye');
// const passwordInput = document.getElementById('psswrd');
// let setpasswordVisble  = true;
// function togglePassword(){
//   setpasswordVisble = !setpasswordVisble;
//   passwordInput.setAttribute('type', setpasswordVisble ? "text": "password")
  
// }

// Sign in password input field


// 
function errormessage(){
  const errorMessage = document.getElementById('#errorMessage');
errorMessage.classList.add('active');
}

function checkEnter(event) {
  if (event.key === "Enter") {
      // Call your function or perform the desired action here
      errormessage();
      myFunction();
  }
}

function myFunction() {
  // Your function logic goes here
  console.log("Enter key pressed!");
}

// 





function chatIconcloseOpen(){
  chatCategories.style.display = "block";
  chatIcon.style.display = 'none';
}
chatIcon.addEventListener('click', chatIconcloseOpen);




// POP UP MODAL PAGES FUNCTION
function showPage(pageId) {
  const pages = document.getElementsByClassName('content-container');
  
  // Use forEach to iterate over the NodeList of the Modals
  Array.from(pages).forEach(function(page) {
    page.style.display = 'none';
  });

  document.getElementById(pageId).style.display = 'block';
}


// clos btn
const popUpcontent = ()=>{
  chatCategories.style.display = "none";
  chatIcon.style.display = "block";
  showPage("Message-us");
  
}
const closeBTN = document.querySelectorAll('#closeIcon');
closeBTN.forEach((item)=>{
item.addEventListener('click', popUpcontent)
})

if(chatCategories.style.display == "none"){
  closeBTN.style.display = "none";
  
}else if(chatCategories.style.display == "block"){
  closeBTN.style.display = "block";
}






const otpInputs = document.getElementById('OTP');
const allOTPInputs = otpInputs.querySelectorAll("input");
const submitButton = document.getElementById('submitButton'); // Replace 'submitButton' with the actual ID of your button
submitButton.setAttribute('disabled', "true");

allOTPInputs.forEach((inp, index) => {
  inp.addEventListener('input', (event) => {
    if (event.target.value.length === 1) {
      if (index < allOTPInputs.length - 1) {
        event.target.nextElementSibling.focus();
      } else {
        // Last input field, enable the button
        submitButton.removeAttribute('disabled');
      }
      setInterval(() => {
        inp.setAttribute('type', "password");
      }, 600);
    }
  });

  inp.addEventListener('keydown', (event) => {
    if (event.key === "Backspace") {
      event.target.value = "";
      if (index > 0) {
        event.target.previousElementSibling.focus();
      } else {
        // First input field, perform your action here
        console.log("First input field reached!");
        // Add your logic for the first input field
      }
      // Disable the button if not all fields are filled
      submitButton.setAttribute('disabled', 'true');
    }
  });
});



// CONFIRM SIGN-IN PAGE
// const otpInputs = document.getElementById('OTP');
// const allOTPInputs = otpInputs.querySelectorAll("input");  
// allOTPInputs.forEach(inp =>{
//   inp.addEventListener('input', (EVENT) =>{
//     if(EVENT.target.value.length === 1){
//       EVENT.target.nextElementSibling.focus();
//       setInterval(()=>{inp.setAttribute('type', "password")}, 600);
//     }
//   })
//   inp.addEventListener('keydown', (EVENT)=>{
//     if(EVENT.key === "Backspace"){
//       EVENT.target.value = "";
//       EVENT.target.previousElementSibling.focus();
//     }
//   })
// })

