/* Adventure Kid Waveforms (AKWF) converted for use with Teensy Audio Library 
*  
*  Adventure Kid Waveforms(AKWF) Open waveforms library
*  https://www.adventurekid.se/akrt/waveforms/adventure-kid-waveforms/
*  
*  This code is in the public domain, CC0 1.0 Universal (CC0 1.0)
*  https://creativecommons.org/publicdomain/zero/1.0/
*
*  Converted by Brad Roy, https://github.com/prosper00
*/

/* AKWF_stereo_0179 256 samples
                                                                                                                        
  +-----------------------------------------------------------------------------------------------------------------+   
  | **   ****                                                                         ***   **                      |   
  |**       ****                                                                    ***      **                     |   
  |*           ****                                                                **         **                    |   
  |*               ****                                                           **           *                    |   
  |                    *****     *****      ******       *****                   **             *                   |   
  |                        **    *   ********    *********    **                 *              **                  |   
  |                         *   *                              **               **               *                  |   
  |                         **  *                               **              *                 *                 |   
  |                          ***                                 **            **                 *                 |   
  |                           **                                  **           *                   *               *|   
  |                                                                **  *      **                   **              *|   
  |                                                                  ******   *                     ***       *** **|   
  |                                                                        ****                       **     ** *** |   
  |                                                                                                    **   **      |   
  |                                                                                                     *** *       |   
  +-----------------------------------------------------------------------------------------------------------------+   
                                                                                                                        
                                                                                                                        
*/


const uint16_t AKWF_stereo_0179 [] = {
33936, 39044, 39511, 48236, 44294, 52625, 47692, 56876, 50104, 58761, 51695, 60252, 52858, 60449, 53634, 60597,
54242, 60095, 54582, 59660, 54822, 58877, 54817, 58073, 54707, 56993, 54413, 55831, 54079, 54493, 53657, 52987,
53292, 51375, 52894, 49553, 52524, 47617, 52104, 45521, 51682, 43570, 51144, 41832, 50549, 40824, 49895, 40685,
49202, 41688, 48467, 43504, 47753, 45985, 47098, 48687, 46515, 51607, 46058, 54544, 45726, 57557, 45466, 60306,
45205, 62593, 44924, 64210, 44550, 65187, 44062, 65535, 43461, 65439, 42818, 65019, 42154, 64337, 41560, 63500,
41084, 62616, 40723, 61711, 40428, 60763, 40196, 59868, 39974, 59011, 39760, 58229, 39567, 57555, 39430, 57065,
39348, 56669, 39309, 56314, 39278, 55946, 39169, 55482, 38892, 54829, 38376, 54030, 37569, 53040, 36435, 51855,
35005, 50526, 33318, 49103, 31422, 47560, 29373, 45903, 27271, 44142, 25238, 42229, 23495, 40146, 22333, 37962,
22095, 35741, 23034, 33524, 25187, 31374, 28240, 29274, 31603, 27136, 34686, 24894, 36976, 22509, 38347, 20006,
38912, 17466, 38864, 14967, 38468, 12574, 37940, 10368, 37418,  8375, 36951,  6575, 36503,  4943, 36022,  3478,
35528,  2229, 35100,  1315, 34858,   911, 34841,  1054, 34988,  1625, 35138,  2455, 35134,  3331, 34895,  4053,
34464,  4550, 33996,  4876, 33720,  5069, 33827,  5193, 34346,  5322, 35175,  5472, 36096,  5550, 36895,  5550,
37456,  5484, 37754,  5316, 37819,  5105, 37718,  4909, 37517,  4702, 37275,  4444, 37018,  4143, 36743,  3728,
36447,  3137, 36124,  2414, 35782,  1676, 35446,  1021, 35142,   643, 34877,   774, 34664,  1562, 34505,  3151,
34390,  5764, 34322,  9570, 34317, 14521, 34359, 20342, 34450, 26463, 34581, 32305, 34733, 37369, 34899, 41536,
35075, 44876, 35279, 47508, 35548, 49626, 35908, 51369, 36380, 52832, 36945, 54044, 37532, 55133, 38051, 56085,
38409, 56896, 38525, 57581, 38363, 58167, 37937, 58767, 37277, 59432, 36431, 60185, 35451, 61029, 34376, 61863,
33214, 62538, 31993, 62993, 30723, 63203, 29406, 63143, 28066, 62879, 26704, 62520, 25332, 62107, 23968, 61659,
22600, 61193, 21219, 60678, 19821, 60020, 18428, 59201, 17117, 58270, 16027, 57212, 15300, 56026, 14988, 54764,
15047, 53387, 15347, 51821, 15698, 50079, 15919, 48134, 15930, 45949, 15707, 43524, 15261, 40927, 14671, 38191,
14024, 35350, 13366, 32527, 12697, 29786, 12012, 27106, 11265, 24486, 10406, 21916,  9601, 19569,  9186, 17842,
 9537, 17229, 10914, 18018, 13311, 20108, 16376, 22998, 19596, 25957, 22679, 28431, 25530, 30133, 28246, 31041,
31035, 31306, 33942, 31089, 36808, 30488, 39463, 29570, 41734, 28378, 43521, 26935, 44879, 25276, 45895, 23458,
46681, 21524, 47350, 19518, 47984, 17486, 48630, 15502, 49319, 13639, 50053, 11955, 50799, 10543, 51535,  9445,
52260,  8728, 52925,  8554, 53490,  9135, 53947, 10588, 54263, 12893, 54391, 15850, 54347, 19064, 54152, 22090,
53795, 24641, 53279, 26506, 52623, 27613, 51786, 28050, 50694, 27925, 49353, 27350, 47752, 26408, 45875, 25193,
43785, 23747, 41543, 22121, 39173, 20361, 36714, 18581, 34206, 16806, 31687, 15177, 29159, 13751, 26685, 12676,
24303, 12014, 22048, 11930, 19980, 12391, 18128, 13359, 16511, 14667, 15105, 16154, 13878, 17562, 12736, 18787,
11655, 19759, 10555, 20450,  9428, 20904,  8257, 21179,  7093, 21373,  5920, 21459,  4816, 21576,  3767, 21648,
 2763, 21795,  1791, 21871,  1039, 22074,   717, 22202,  1114, 22482,  2409, 22676,  4533, 23021,  7121, 23155,
 9668, 23268, 11826, 23012, 13279, 22625, 14035, 21838, 14148, 20976, 13863, 19863, 13164, 18742, 12366, 17542,
11449, 16412, 10749, 15506, 10362, 14977, 10934, 15562, 12575, 17246, 16001, 21270, 20863, 26388, 27341, 34363,
};