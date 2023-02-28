function clse(id_vac, status){
    if(parseInt(status)==1){
        var data = confirm("Закрити набір?")
        }
    else {
        var data = confirm("Відкрити набір?")
    }
    if(data){
        window.location.href = '/expert/vacancy=' + id_vac.toString() + '/set_status='+status.toString()+'/close';
    }
}
function dlte(ref){
    var data = confirm("Ви підтверджуєте видалення?")
    console.log(data)
    if(data==true){
        window.location.href = ref;
    }
}
function genPDF(name_vac){
    var element = document.getElementById("cnt");
    console.log(element)
    const date = new Date();


     var opt = {
                margin:       1,
                pagebreak: { mode: 'avoid-all', before: '#secondpage' },
                filename:     'candidate_'+name_vac+'_'+date.getDate().toString()+'.'+date.getMonth().toString()+'.'+date.getFullYear().toString()+'.pdf',
                html2canvas:  { scale: 2 },
                jsPDF:        { unit: 'cm', format: 'a4', orientation: 'l' }
              };
       //html2pdf().from(element).save();
      html2pdf().set(opt).from(element).save();
  }
