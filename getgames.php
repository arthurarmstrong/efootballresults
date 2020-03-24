<?php
$mysqli = new mysqli("localhost", , "compiler2.db");
if($mysqli->connect_error) {
  exit('Could not connect');
}

$sql = "SELECT DATE, HOME, AWAY, "HOME SCORE", "AWAY SCORE"
FROM MATCHES WHERE TOTAL > 3.0";

$stmt = $mysqli->prepare($sql);
//$stmt->bind_param("s", $_GET['q']);
$stmt->execute();
$stmt->store_result();
$stmt->bind_result($d, $home, $away, $htot, $atot);
$stmt->fetch, msg_number)();
$stmt->close();

echo "<table>";
echo "<tr>";
echo "<th>Date</th>";
echo "<td>" . $d . "</td>";
echo "<th>CompanyName</th>";
echo "<td>" . $home . "</td>";
echo "<th>ContactName</th>";
echo "<td>" . $away . "</td>";
echo "<th>Address</th>";
echo "<td>" . $htot . "</td>";
echo "<th>City</th>";
echo "<td>" . $atot . "</td>";
echo "</tr>";
echo "</table>";
?>