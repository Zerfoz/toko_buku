function validateForm() {
    var nama = document.getElementById("nama");
    var npm = document.getElementById("npm");
    var tugas = document.getElementById("tugas");
    var uts = document.getElementById("uts");
    var uas = document.getElementById("uas");
    var isValid = true;

    if (nama.value === "") {
        nama.classList.add("is-invalid");
        isValid = false;
    } else {
        nama.classList.remove("is-invalid");
    }

    if (npm.value === "") {
        npm.classList.add("is-invalid");
        isValid = false;
    } else {
        npm.classList.remove("is-invalid");
    }

    if (tugas.value === "") {
        tugas.classList.add("is-invalid");
        isValid = false;
    } else {
        tugas.classList.remove("is-invalid");
    }

    if (uts.value === "") {
        uts.classList.add("is-invalid");
        isValid = false;
    } else {
        uts.classList.remove("is-invalid");
    }

    if (uas.value === "") {
        uas.classList.add("is-invalid");
        isValid = false;
    } else {
        uas.classList.remove("is-invalid");
    }

    if (!isValid) {
        alert("Form input belum diisi");
    }

    return isValid;
}