//Jquery / config for datatables
$(document).ready(function() {
  var table = $('#assets').DataTable( {

    //scrolling
    "scrollY": "500px",
    "scrollX": true,
    "scrollCollapse": true,
    "paging": false,

    //buttons
    "lengthChange": false,
    "buttons": [ 'excel', 'pdf', 'colvis' ],

    //classes
    "columnDefs": [ {
      "targets"  : 'no-sort',
      "orderable": false
    },
    {
      "targets": "default_hidden",
      "visible": false
    } ]

  } );

  table.buttons().container().appendTo('#assets_wrapper .col-sm-6:eq(0)');

} );

//open modal on asset click
$(document).ready(function() {
  var table = $('#assets').DataTable();

  $('#assets tbody').on( 'click', 'tr', function () {
    var data = table.row(this).data();

    var modal = $('#assetInspectModal');
    modal.modal('show');

    //display current row data in form
    $(".modal-body #AssetFormUID").val(data[0]);
    $(".modal-body #AssetFormModel").val(data[2]);
    $(".modal-body #AssetFormMake").val(data[1]);
    $(".modal-body #AssetFormSerial").val(data[3]);
    $(".modal-body #AssetFormIp").val(data[4]);
    $(".modal-body #AssetFormMac").val(data[5]);
    $(".modal-body #AssetFormDateIssued").val(data[6]);
    $(".modal-body #AssetFormDateRenewal").val(data[7]);
    $(".modal-body #AssetFormCondition").val(data[8]);
    $(".modal-body #AssetFormOwner").val(data[9]);
    $(".modal-body #AssetFormLocation").val(data[10]);
    $(".modal-body #AssetFormNotes").val(data[11]);
    $(".modal-body #AssetFormState").val(data[12]);
    $(".modal-body #AssetFormKind").val(data[13]);
    $(".modal-body #AssetFormCost").val(data[14]);
    $(".modal-body #AssetFormCurrency").val(data[15]);

    //open confirm delete modal and pass data
    $('#assetDeleteButton').on('click', function () {
      modal.modal('hide');

      var target = "/api/delete/asset/" + data[0]

      $('#confirmDeleteModal').modal('show');
      $("#confirmDeleteButton").prop("href",target);

    }); //end asset delete confirm

  }); //end inspect modal open

});
