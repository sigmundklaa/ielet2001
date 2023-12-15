<?php
$base_path = 'wp-content/uploads/raspberry/images';

// Filter out directory and get the list of files
$files = array_diff(scandir($base_path, SCANDIR_SORT_DESCENDING), array('..', '.'));

// English to Norwegian month translations
$monthTranslations = [
    'January' => 'Januar',
    'February' => 'Februar',
    'March' => 'Mars',
    'April' => 'April',
    'May' => 'Mai',
    'June' => 'Juni',
    'July' => 'Juli',
    'August' => 'August',
    'September' => 'September',
    'October' => 'Oktober',
    'November' => 'November',
    'December' => 'Desember'
];

if ($files) {
    $latest_file = $files[0];
    $full_path = $base_path . "/" . $latest_file;

    // Get the date in English format with a punctuation mark for the day
    $timestamp = filemtime($full_path);
    $timestampPlusOneHour = $timestamp + 3600; // Add one hour as the server time is GMT.
    $englishDate = date("d. F Y H:i.", $timestampPlusOneHour);

    // Translate the month name to Norwegian
    foreach ($monthTranslations as $english => $norwegian) {
        $englishDate = str_replace($english, $norwegian, $englishDate);
    }

    echo "<div style='text-align:center;'>";

    // Display the "Last modified" message (in Norwegian) before the image
    echo "Sist oppdatert: " . $englishDate . "<br><br>";
    
    // Display the latest image
    echo "<img src='../" . $full_path . "' style='display:block; margin: 0 auto; height:90%; width:90%; border: 2px solid black;' />";

    echo "</div>";
} else {
    // Display an error message if no files are found
    echo "Ingen filer funnet i mappen!";
}
?>
