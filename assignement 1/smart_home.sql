SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";

--
-- Database: `home_monitoring`
--
CREATE DATABASE IF NOT EXISTS `gmadotto1` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `gmadotto1`;

-- --------------------------------------------------------

--
-- Struttura della tabella `sensors`
--
DROP TABLE IF EXISTS `sensors`;
CREATE TABLE `sensors` (
  `id` int(11) NOT NULL,
  `timestamp` timestamp NULL DEFAULT current_timestamp(),
  `temperature` float(11) DEFAULT NULL,
  `humidity` float(11) DEFAULT NULL,
  `real_temperature` float(11) DEFAULT NULL,
  `light_value` int(11) DEFAULT NULL,
  `rssi` int(11) DEFAULT NULL
  
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

DROP TABLE IF EXISTS `alerts`;
CREATE TABLE `alerts` (
  `id` int(11) NOT NULL,
  `timestamp` timestamp NULL DEFAULT current_timestamp(),
  `temperature_alert` float(11) DEFAULT NULL,
  `humidity_alert` float(11) DEFAULT NULL,
  `real_temperature_alert` float(11) DEFAULT NULL,
  `light_value_alert` int(11) DEFAULT NULL,
  `rssi_alert` int(11) DEFAULT NULL
  
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Indici per le tabelle `sensors`
--
ALTER TABLE `sensors`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT per la tabella 'sensors'
--
ALTER TABLE `sensors`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
COMMIT;

--
-- Indici per le tabelle `alerts`
--
ALTER TABLE `alerts`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT per la tabella 'alerts'
--
ALTER TABLE `alerts`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
COMMIT;
